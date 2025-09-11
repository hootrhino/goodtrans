# 构建和发布指南

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 2. 一键打包
```bash
python build.py
```

### 3. 初始化Git仓库（首次使用）
```bash
python init_git.py
```

## 打包选项

### 基础打包
```bash
pyinstaller --onefile --windowed main.py
```

### 高级打包（使用build.py）
- 自动清理旧文件
- 包含文档和配置文件
- 创建分发包
- 显示文件大小信息

### 打包输出
- `dist/串口通信工具.exe` - 单个可执行文件
- `dist/串口通信工具_完整包/` - 包含文档的完整分发包

## 文件结构

```
串口通信工具_完整包/
├── 串口通信工具.exe      # 主程序
├── README.md            # 项目说明
├── USAGE.md             # 使用指南
├── PAIRING_GUIDE.md     # 配对指南
└── requirements.txt     # 依赖列表
```

## 发布前检查清单

- [ ] 测试所有功能正常
- [ ] 检查版本号
- [ ] 更新文档
- [ ] 清理测试文件
- [ ] 确认图标文件存在（可选）
- [ ] 测试打包后的可执行文件

## 版本管理

### 版本号格式
使用语义化版本号：MAJOR.MINOR.PATCH
- MAJOR：不兼容的API修改
- MINOR：向下兼容的功能性新增
- PATCH：向下兼容的问题修正

### 发布流程
1. 更新版本号（在代码中）
2. 运行测试
3. 更新CHANGELOG.md
4. 打包
5. 创建Git标签
6. 发布Release

## 常见问题

### 打包文件太大
- 使用`--exclude-module`排除不需要的模块
- 检查是否包含了不必要的依赖
- 使用UPX压缩（需安装UPX）

### 运行时缺少DLL
- 确保所有依赖都已正确安装
- 检查PyInstaller的hiddenimports

### 杀毒软件误报
- 使用代码签名证书
- 提交到杀毒软件白名单

## 开发环境

### 必需工具
- Python 3.7+
- PyInstaller 4.0+
- Git

### 可选工具
- UPX（压缩可执行文件）
- 代码签名工具
- Inno Setup（创建安装程序）

## 自动化构建

### GitHub Actions示例
```yaml
name: Build
on: [push, pull_request]
jobs:
  build:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller
    - name: Build executable
      run: python build.py
```