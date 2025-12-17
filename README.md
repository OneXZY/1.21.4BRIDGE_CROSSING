# Minecraft 1.21.4 Nether Fortress Quad Crossing Finder

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

### Description

A Python tool to find **Quad Crossings** (2x2 adjacent BridgeCrossing pieces) in Minecraft 1.21.4 Nether Fortresses for any given seed.

A Quad Crossing is a rare formation where 4 BridgeCrossing pieces are perfectly aligned and directly adjacent, forming a large square intersection.

### Requirements

- Python 3.7+
- No external dependencies

### Usage

#### Basic Usage

```bash
# Search for quad crossings with default range (5000 blocks)
python main.py <seed>

# Example
python main.py 12345
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--range` | Search radius in blocks | 5000 |
| `--center X Z` | Search center coordinates | 0 0 |
| `--verbose` | Show detailed output | False |
| `--analyze X Z` | Analyze specific chunk | - |

#### Examples

```bash
# Search within 10000 blocks of spawn
python main.py 12345 --range 10000

# Search around specific coordinates
python main.py 12345 --center 5000 3000 --range 8000

# Show detailed generation info
python main.py 12345 --verbose

# Analyze a specific fortress
python main.py 12345 --analyze 207 176
```

### Output

```
--- Quad Crossing #1 ---
Fortress chunk: (207, 176)
Fortress block: (3312, 2816)
Total crossings in fortress: 5

Quad crossing details:
  Center: X=3332, Y=68, Z=2836
  Range: (3314, 2818) -> (3351, 2855)

  Individual crossing positions:
    1. X=3323, Y=68, Z=2827 (type: StartPiece)
    2. X=3342, Y=68, Z=2827 (type: BridgeCrossing)
    3. X=3323, Y=68, Z=2846 (type: BridgeCrossing)
    4. X=3342, Y=68, Z=2846 (type: BridgeCrossing)
```

### In-Game Verification

1. Create a world with the specified seed
2. Go to the Nether
3. Teleport to the coordinates: `/tp <X> 68 <Z>`
4. Verify the quad crossing exists

### File Structure

```
├── main.py                 # Entry point
├── fortress_locator.py     # Fortress position calculation
├── fortress_generator.py   # Structure piece generation
├── crossing_detector.py    # Quad crossing detection
├── random_source.py        # Minecraft random number generator
└── README.md               # This file
```

### Technical Details

- Based on Minecraft 1.21.4 decompiled source code
- Uses `RandomSpreadStructurePlacement` (spacing=27, separation=4, salt=30084232)
- Implements `LegacyRandomSource` for accurate random number generation
- Correctly distinguishes between Fortress (weight=2) and Bastion Remnant (weight=3)

---

<a name="中文"></a>
## 中文

### 简介

一个用于在 Minecraft 1.21.4 下界要塞中寻找**四联十字路口**（2x2相邻的BridgeCrossing部件）的 Python 工具。

四联十字路口是一种罕见的结构，由4个完全对齐且直接相邻的十字路口部件组成，形成一个大型的正方形交叉口。

### 环境要求

- Python 3.7+
- 无需外部依赖

### 使用方法

#### 基本用法

```bash
# 使用默认范围（5000方块）搜索四联十字路口
python main.py <种子>

# 示例
python main.py 12345
```

#### 参数选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--range` | 搜索半径（方块） | 5000 |
| `--center X Z` | 搜索中心坐标 | 0 0 |
| `--verbose` | 显示详细输出 | False |
| `--analyze X Z` | 分析指定区块 | - |

#### 使用示例

```bash
# 在出生点附近10000方块范围内搜索
python main.py 12345 --range 10000

# 从指定坐标附近搜索
python main.py 12345 --center 5000 3000 --range 8000

# 显示详细生成信息
python main.py 12345 --verbose

# 分析特定要塞
python main.py 12345 --analyze 207 176
```

### 输出说明

```
--- Quad Crossing #1 ---
Fortress chunk: (207, 176)        # 要塞区块坐标
Fortress block: (3312, 2816)      # 要塞方块坐标
Total crossings in fortress: 5    # 要塞中十字路口总数

Quad crossing details:
  Center: X=3332, Y=68, Z=2836    # 四联十字路口中心坐标
  Range: (3314, 2818) -> (3351, 2855)  # 范围

  Individual crossing positions:   # 各十字路口位置
    1. X=3323, Y=68, Z=2827 (type: StartPiece)
    2. X=3342, Y=68, Z=2827 (type: BridgeCrossing)
    3. X=3323, Y=68, Z=2846 (type: BridgeCrossing)
    4. X=3342, Y=68, Z=2846 (type: BridgeCrossing)
```

### 游戏内验证

1. 使用指定种子创建世界
2. 进入下界
3. 传送到坐标：`/tp <X> 68 <Z>`
4. 确认四联十字路口存在

### 文件结构

```
├── main.py                 # 程序入口
├── fortress_locator.py     # 要塞位置计算
├── fortress_generator.py   # 结构部件生成
├── crossing_detector.py    # 四联十字路口检测
├── random_source.py        # Minecraft随机数生成器
└── README.md               # 本文件
```

### 技术细节

- 基于 Minecraft 1.21.4 反编译源代码
- 使用 `RandomSpreadStructurePlacement`（间距=27，分隔=4，盐值=30084232）
- 实现 `LegacyRandomSource` 以确保随机数生成准确
- 正确区分要塞（权重=2）和堡垒遗迹（权重=3）

---

## License

MIT License
