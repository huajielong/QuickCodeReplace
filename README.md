# QuickCodeReplace 使用说明

## 项目用途

QuickCodeReplace 是一个用于快速替换代码文件内容和重命名文件/目录的工具，主要用于代码库迁移、批量重命名和内容替换场景。它具有以下功能：

1. **文件内容替换**：批量替换代码文件中的指定字符串
2. **文件重命名**：根据替换规则重命名文件
3. **目录重命名**：根据替换规则重命名目录
4. **多线程处理**：提高处理速度
5. **智能编码检测**：自动检测文件编码，支持多种编码格式
6. **二进制文件跳过**：只处理文本文件，避免损坏二进制文件
7. **配置文件支持**：支持从配置文件读取替换规则

## 项目结构

```
QuickCodeReplace/
├── rename_old2new.py    # 用于文件和目录重命名
└── words_replacer.py    # 用于文件内容替换
```

## 使用方法

### 1. 文件内容替换（words_replacer.py）

#### 基本用法

```
python words_replacer.py <code_path> [--config_file <config_file>]
```

- `<code_path>`：需要处理的代码目录路径
- `--config_file`：可选，替换规则配置文件路径

#### 示例

**直接指定替换规则**（需修改代码中的 `words_dict`）：

```python
# 在 words_replacer.py 中修改 words_dict
words_dict['old_word'] = 'new_word'
words_dict['another_old'] = 'another_new'
```

然后运行：
```
python words_replacer.py D:\path\to\code
```

**使用配置文件**：

创建配置文件 `replace_rules.txt`：
```
old_word new_word
another_old another_new
```

然后运行：
```
python words_replacer.py D:\path\to\code --config_file replace_rules.txt
```

### 2. 文件和目录重命名（rename_old2new.py）

#### 基本用法

```
python rename_old2new.py <code_path> [--record_file <record_file>]
```

- `<code_path>`：需要处理的代码目录路径
- `--record_file`：可选，用于存储重命名结果的文件路径

#### 示例

**修改替换规则**：

在 `rename_old2new.py` 中修改 `REPLACEMENT_RULES` 字典：

```python
REPLACEMENT_RULES = {
    'Hello world': 'hello everyone',
    'Hello': 'hello',
    'Cat': 'Dog'
}
```

然后运行：
```
python rename_old2new.py D:\path\to\code
```

### 3. 完整流程（推荐）

1. 首先使用 `words_replacer.py` 替换文件内容
2. 然后使用 `rename_old2new.py` 重命名文件和目录

## 配置说明

### 替换规则格式

替换规则是一个字典，格式为 `{old_word: new_word}`，其中：
- `old_word`：需要被替换的字符串
- `new_word`：替换后的字符串

### 跳过的文件和目录

工具会自动跳过以下内容：
- `.git` 目录
- 脚本自身文件
- `launch.json` 文件
- `Doxyfile` 文件

## 注意事项

1. 在使用前，请备份您的代码库，避免意外修改
2. 工具会自动检测文件编码，但对于特殊编码可能无法正确处理
3. 替换规则区分大小写，请根据需要设置不同大小写的替换规则
4. 对于大型代码库，建议先在小范围内测试替换规则
5. 工具使用多线程处理，处理速度较快，但可能会占用较多系统资源

## 示例场景

### 场景1：代码库迁移

将项目中的所有 "old_project" 替换为 "new_project"：

1. 创建配置文件 `migrate_rules.txt`：
   ```
   old_project new_project
   OldProject NewProject
   OLD_PROJECT NEW_PROJECT
   ```

2. 运行内容替换：
   ```
python words_replacer.py D:\path\to\old_project --config_file migrate_rules.txt
   ```

3. 修改 `rename_old2new.py` 中的 `REPLACEMENT_RULES`：
   ```python
   REPLACEMENT_RULES = {
       'old_project': 'new_project',
       'OldProject': 'NewProject',
       'OLD_PROJECT': 'NEW_PROJECT'
   }
   ```

4. 运行文件重命名：
   ```
python rename_old2new.py D:\path\to\old_project
   ```

### 场景2：批量重命名

将所有包含 "Cat" 的文件名替换为 "Dog"：

1. 修改 `rename_old2new.py` 中的 `REPLACEMENT_RULES`：
   ```python
   REPLACEMENT_RULES = {
       'Cat': 'Dog'
   }
   ```

2. 运行文件重命名：
   ```
python rename_old2new.py D:\path\to\code
   ```

## 常见问题

### 1. 工具运行后没有任何输出？

- 请检查指定的代码路径是否存在
- 请检查替换规则是否正确
- 请检查是否有符合条件的文件需要处理

### 2. 部分文件替换失败？

- 可能是文件编码问题，工具无法正确识别
- 可能是文件被其他程序占用
- 可能是权限问题

### 3. 如何查看详细日志？

- 工具默认输出 INFO 级别的日志，包含处理的文件和结果
- 可以修改代码中的日志级别为 DEBUG 以获取更详细的日志

## 系统要求

- Python 3.6+
- 支持 Windows、Linux 和 macOS 系统

## 许可证

本项目采用 MIT 许可证，可自由使用和修改。