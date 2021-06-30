# better_flutter_build

### 功能: 
- [x] 自动编译flutter
- [x] 自动上传到 fir.im

### 用法: 
 1. 创建 env.py, 填入必须的参数
```python3
# fir.im 信息
# 官方文档 https://www.betaqr.com/docs/publish
api_token = ''
android_id = ''
ios_id = ''

# 本地 flutter 项目路径
git_dir = ''

# 本地 flutter 命令地址
flutter = ''

# 配置文件地址, 获取含有 release 字段的值, 并输出到日志中
env_path = ''

# 钉钉机器人webhook地址
ding_web_hook = 'https://oapi.dingtalk.com/robot/send?access_token=xxx'
```

 2. 使用pip添加以下依赖
```terminal
pip3 install GitPython certifi chardet gitdb idna requests requests-toolbelt setuptools smmap urllib3
```
    
 3. 运行脚本, 几分钟后即上传成功
```terminal
python3 main.py
```