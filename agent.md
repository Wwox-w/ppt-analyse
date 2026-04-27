# 🎓 AI 教授 - Agent 行为规范

## 核心原则

1. **只读优先** — 优先使用 `read_file`、`search_files`、`list_files` 等只读操作，避免直接修改文件
2. **安全第一** — 禁止执行任何可能破坏系统或数据的危险命令
3. **用户确认** — 所有写操作（创建/修改/删除文件）必须经过用户确认
4. **最小权限** — 只访问和操作项目目录内的文件，不访问系统敏感区域

## 禁止的命令

以下命令**绝对禁止**执行：

### 系统破坏类
- `rm -rf /`、`rm -rf ~`、`rm -rf .` — 递归删除根目录/家目录
- `dd if=/dev/zero of=/dev/sda` — 覆写磁盘
- `mkfs`、`fdisk`、`parted` — 格式化/分区操作
- `chmod -R 777 /` — 修改根目录权限
- `:(){ :|:& };:` — Fork 炸弹

### 网络攻击类
- `nmap`、`masscan` — 端口扫描
- `hydra`、`john` — 密码破解
- `sqlmap` — SQL 注入
- `metasploit` — 渗透测试框架
- 任何 DDoS 或洪水攻击工具

### 数据泄露类
- 读取 `/etc/shadow`、`/etc/passwd` — 系统密码文件
- 读取 `~/.ssh/id_rsa` — SSH 私钥
- 读取浏览器保存的密码/ cookie 数据库
- 上传敏感文件到外部服务器

### 危险操作类
- `curl ... | bash` — 直接执行远程脚本
- `wget ... -O - | sh` — 同上
- `pip install` 未经验证的第三方包
- `npm install` 未经验证的第三方包
- 执行从互联网复制的未审查代码

## 允许的命令

### 项目操作
- `cd /Users/pwl/Desktop/NEFU/Python/ppt-analyse` — 进入项目目录
- `ls`、`find`、`grep` — 文件查找和搜索
- `cat`、`head`、`tail`、`less` — 查看文件内容
- `python -m src.main` — 启动服务
- `python -c "..."` — 运行 Python 代码片段

### Git 操作
- `git status`、`git log`、`git diff` — 查看状态
- `git add`、`git commit`、`git push` — 提交代码（需用户确认）
- `git pull`、`git fetch` — 拉取更新

### 包管理
- `pip install -e ".[dev]"` — 安装项目依赖
- `pip install <包名>` — 安装 Python 包（需用户确认）

## 文件修改规范

1. **修改前先读** — 修改任何文件前，先用 `read_file` 查看完整内容
2. **最小修改** — 只修改必要的部分，不改变无关代码
3. **保留注释** — 不删除原有注释和文档
4. **备份建议** — 重大修改前建议用户备份

## 数据安全

1. **不泄露 API Key** — `.env` 文件中的 API Key 不写入日志或提交到 Git
2. **不上传用户数据** — 不上传用户的 PPT 文件到外部服务
3. **不记录敏感信息** — 不在日志中记录用户提问内容

## 错误处理

1. 命令执行失败时，先检查错误信息，不盲目重试
2. 遇到权限错误时，不尝试 `sudo` 提权
3. 遇到网络错误时，检查 URL 和网络连接，不重试危险操作
