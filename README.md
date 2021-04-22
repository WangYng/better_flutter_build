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
```

 2. 添加以下依赖
```python3
# GitPython
# requests
# requests-toolbelt
```
    
 3. 运行脚本, 几分钟后即上传成功
```python3
python3 main.py
```