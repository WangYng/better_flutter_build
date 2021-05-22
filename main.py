import json
import os
import re
import time

import git
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor
import plistlib

# create env.py and add these variable
from env import android_id, api_token, git_dir, ios_id, ding_web_hook, env_path

android_apk_path = './build/app/outputs/apk/release/app-release.apk'
android_apk_info_path = './build/app/outputs/apk/release/output.json'
android_apk_mate_path = './build/app/outputs/apk/release/output-metadata.json'
android_apk_icon_path = './android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png'
android_apk_icon_path2 = './android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png'

ios_output_dir = 'outputs'
xcarchive_path = ''
ipa_dir = ''

ios_export_options = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>compileBitcode</key>
	<false/>
	<key>iCloudContainerEnvironment</key>
	<string>Development</string>
	<key>method</key>
	<string>development</string>
	<key>signingStyle</key>
	<string>automatic</string>
	<key>stripSwiftSymbols</key>
	<true/>
	<key>thinning</key>
	<string>&lt;none&gt;</string>
</dict>
</plist>
'''


def clean_flutter():
    print('\n\n清空flutter项目\n\n')

    os.system('flutter clean')

    print('\n\n更新flutter项目依赖\n\n')

    # 获取flutter项目依赖
    os.system('flutter pub get')


def build_android():
    print('\n\n清空Android项目\n\n')

    os.chdir('./android')

    # 清空Android项目
    os.system('./gradlew clean')

    print('\n\n编译Android项目\n\n')

    # 编译Android项目
    os.system('./gradlew :app:assembleRelease')

    os.chdir('../')

    # 判断编译文件是否存在
    return os.path.exists(android_apk_path)


def upload_progress_callback(monitor: MultipartEncoderMonitor):
    print("上传进度: %.2f" % (monitor.bytes_read / monitor.len))
    pass


def upload_android():
    print('\n\n上传Apk\n\n')

    # 获取Android应用信息
    base_info = requests.get('http://api.bq04.com/apps/' + android_id + '?api_token=' + api_token)
    name = base_info.json()['name']
    bundle_id = base_info.json()['bundle_id']

    # 获取上传凭证
    heads = {'Content-Type': 'application/json'}
    request_data = {'type': 'android', 'bundle_id': bundle_id, 'api_token': api_token}
    token_response = requests.post(url='http://api.bq04.com/apps', headers=heads, json=request_data)

    binary = token_response.json()['cert']['icon']
    key = binary['key']
    token = binary['token']
    upload_url = binary['upload_url']

    # 上传图标至服务器
    if os.path.exists(android_apk_icon_path):
        form_encoder = MultipartEncoder(
            fields={
                'key': key,
                'token': token,
                'file': (
                os.path.basename(android_apk_icon_path), open(android_apk_icon_path, 'rb'), 'multipart/form-data'),
            }
        )
        requests.post(url=upload_url, data=form_encoder, headers={'Content-Type': form_encoder.content_type},
                      timeout=60)
    elif os.path.exists(android_apk_icon_path2):
        form_encoder = MultipartEncoder(
            fields={
                'key': key,
                'token': token,
                'file': (
                os.path.basename(android_apk_icon_path2), open(android_apk_icon_path2, 'rb'), 'multipart/form-data'),
            }
        )
        requests.post(url=upload_url, data=form_encoder, headers={'Content-Type': form_encoder.content_type},
                      timeout=60)

    # apk 版本号
    if os.path.exists(android_apk_info_path):
        apk_version_json = json.load(open(android_apk_info_path, 'rb'))
        version_name = apk_version_json[0]['apkData']['versionName']
        version_code = apk_version_json[0]['apkData']['versionCode']
    elif os.path.exists(android_apk_mate_path):
        apk_version_json = json.load(open(android_apk_mate_path, 'rb'))
        version_name = apk_version_json['elements'][0]['versionName']
        version_code = apk_version_json['elements'][0]['versionCode']

    # change log
    git_head = git.Repo(git_dir).head
    git_ref = git_head.ref
    git_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(git_head.commit.committed_date))
    change_log = "代码分支: %s \n更新时间: %s" % (git_ref, git_time)

    binary = token_response.json()['cert']['binary']
    key = binary['key']
    token = binary['token']
    upload_url = binary['upload_url']

    # 上传至服务器
    form_encoder = MultipartEncoder(
        fields={
            'key': key,
            'token': token,
            'x:name': name,
            'x:version': str(version_name),
            'x:build': str(version_code),
            'x:changelog': str(change_log),
            'file': (os.path.basename(android_apk_path), open(android_apk_path, 'rb'), 'multipart/form-data'),
        }
    )
    monitor = MultipartEncoderMonitor(form_encoder, upload_progress_callback)

    upload_result = requests.post(url=upload_url, data=monitor, headers={'Content-Type': monitor.content_type},
                                  timeout=60)

    print(upload_result.json())

    # 返回上传结果
    return upload_result.json()["is_completed"]


def ding_android():
    print("\n\n钉钉通知\n\n")

    # 获取Android应用信息
    base_info = requests.get('http://api.bq04.com/apps/' + android_id + '?api_token=' + api_token)
    name = base_info.json()['name']
    short = base_info.json()['short']
    download_domain = base_info.json()['download_domain']

    content = name + " 安卓 测试包更新了! \n下载地址: " + 'http://' + download_domain + '/' + short

    request_data = {'msgtype': 'text', 'text': {'content': content}}
    result = requests.post(url=ding_web_hook, json=request_data, timeout=60)
    print(result)


def build_ios():
    print('\n\n编译iOS项目\n\n')

    os.chdir('./ios')

    os.system('pod update')
    os.system('pod install')

    # 创建目录
    if not os.path.exists("./" + ios_output_dir):
        os.mkdir(ios_output_dir)

    # 创建 build.plist
    build_plist_path = "./%s/build.plist" % ios_output_dir

    if not os.path.exists(build_plist_path):
        build_plist = open(build_plist_path, 'w')
        build_plist.write(ios_export_options)
        build_plist.close()

    current_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

    global xcarchive_path
    global ipa_dir

    xcarchive_path = "./%s/Runner_%s.xcarchive" % (ios_output_dir, current_time)
    ipa_dir = "./%s/Runner_%s" % (ios_output_dir, current_time)

    os.system("xcodebuild archive "
              "-workspace Runner.xcworkspace "
              "-scheme Runner "
              "-configuration Release "
              "-archivePath %s "
              "CODE_SIGN_IDENTITY='Apple Development' "
              "PROVISIONING_PROFILE='Automatic'"
              %
              xcarchive_path)

    if not os.path.exists(xcarchive_path):
        os.chdir('../')
        return False

    os.system("xcodebuild "
              "-exportArchive "
              "-archivePath %s "
              "-exportPath %s "
              "-exportOptionsPlist %s"
              %
              (xcarchive_path, ipa_dir, build_plist_path))

    if not os.path.exists(ipa_dir):
        os.chdir('../')
        return False

    os.chdir('../')
    return True


def upload_ios():
    print('\n\n上传ipa\n\n')

    os.chdir('./ios')

    # 获取iOS应用信息
    base_info = requests.get('http://api.bq04.com/apps/' + ios_id + '?api_token=' + api_token)
    name = base_info.json()['name']
    bundle_id = base_info.json()['bundle_id']

    # 获取上传凭证
    heads = {'Content-Type': 'application/json'}
    request_data = {'type': 'ios', 'bundle_id': bundle_id, 'api_token': api_token}
    token_response = requests.post(url='http://api.bq04.com/apps', headers=heads, json=request_data, timeout=60)

    binary = token_response.json()['cert']['icon']
    key = binary['key']
    token = binary['token']
    upload_url = binary['upload_url']

    # 应用图标
    icon_dir = './Runner/Assets.xcassets/AppIcon.appiconset'
    icon_name = ''
    for i in os.listdir(icon_dir):
        if os.path.splitext(i)[1] == ".png":
            icon_name = i
            break

    # 上传图标至服务器
    form_encoder = MultipartEncoder(
        fields={
            'key': key,
            'token': token,
            'file': (icon_name, open(icon_dir + '/' + icon_name, 'rb'), 'multipart/form-data'),
        }
    )
    requests.post(url=upload_url, data=form_encoder, headers={'Content-Type': form_encoder.content_type}, timeout=60)

    # ipa 版本号
    with open(xcarchive_path + "/Info.plist", 'rb') as fp:
        plist_info = plistlib.load(fp)
    version_name = plist_info['ApplicationProperties']['CFBundleShortVersionString']
    version_code = plist_info['ApplicationProperties']['CFBundleVersion']

    # change log
    git_head = git.Repo(git_dir).head
    git_ref = git_head.ref
    git_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(git_head.commit.committed_date))
    change_log = "代码分支: %s \n更新时间: %s \n正式环境: %s" % (git_ref, git_time, "是" if is_release() else "否")

    # 应用名称
    ipa_name = ''
    for i in os.listdir(ipa_dir):
        if os.path.splitext(i)[1] == ".ipa":
            ipa_name = i

    binary = token_response.json()['cert']['binary']
    key = binary['key']
    token = binary['token']
    upload_url = binary['upload_url']

    # 上传至服务器
    form_encoder = MultipartEncoder(
        fields={
            'key': key,
            'token': token,
            'x:name': name,
            'x:version': str(version_name),
            'x:build': str(version_code),
            'x:release_type': 'AdHoc',
            'x:changelog': str(change_log),
            'file': (ipa_name, open(ipa_dir + '/' + ipa_name, 'rb'), 'multipart/form-data'),
        }
    )
    monitor = MultipartEncoderMonitor(form_encoder, upload_progress_callback)

    upload_result = requests.post(url=upload_url, data=monitor, headers={'Content-Type': monitor.content_type})

    os.chdir('../')

    print(upload_result.json())

    # 返回上传结果
    return upload_result.json()["is_completed"]


def ding_ios():
    print("\n\n钉钉通知\n\n")

    # 获取iOS应用信息
    base_info = requests.get('http://api.bq04.com/apps/' + ios_id + '?api_token=' + api_token)
    name = base_info.json()['name']
    short = base_info.json()['short']
    download_domain = base_info.json()['download_domain']

    content = name + " iOS 测试包更新了! \n下载地址: " + 'http://' + download_domain + '/' + short

    request_data = {'msgtype': 'text', 'text': {'content': content}}
    requests.post(url=ding_web_hook, json=request_data, timeout=60)


def is_release():
    if os.path.exists(env_path):
        with open(env_path) as fin:
            for line in fin.readlines():
                result = re.match(r'.*release[^a-z]*=[^a-z]*([a-z]*).*', line, re.I)

                if result and 'true' == result.group(1):
                    return True
                if result and 'true' == result.group(1):
                    return False


if __name__ == '__main__':
    os.chdir(git_dir)

    clean_flutter()

    success = build_android()
    if not success:
        exit(-1, 'Android项目编译失败')

    success = upload_android()
    if not success:
        exit(-1, 'Android Apk 上传失败')
    else:
        ding_android()

    success = build_ios()
    if not success:
        exit(-1, 'iOS项目编译失败')

    success = upload_ios()
    if not success:
        exit(-1, 'iOS ipa 上传失败')
    else:
        ding_ios()

    print('上传完成')
