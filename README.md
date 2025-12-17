  基本用法

  # 搜索指定种子的四联十字路口（默认范围5000方块）
  python main.py <种子>

  # 扩大搜索范围（方块坐标）
  python main.py 12345 --range 10000

  # 从指定坐标开始搜索
  python main.py 12345 --center 1000 2000

  # 显示详细输出
  python main.py 12345 --verbose

  # 分析特定区块的要塞结构
  python main.py 12345 --analyze207 176

  # 使用示例

  # 在出生点附近10000方块范围内搜索
  python main.py 1671756613324590989 --range 10000

  # 从下界坐标(5000, 3000)附近搜索
  python main.py 1671756613324590989 --center 5000 3000 --range 8000

  # 查看某个要塞的详细结构
  python main.py 1671756613324590989 --analyze 207 176

