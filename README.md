# ExifFuzzer

A simple black-block、mutation-based exif fuzzer.


# Usage

环境依赖：

- Ubuntu 18.04
- Python 3.9.23


1. 安装项目依赖

```sh
pipenv install
```

2. 编译待测程序

```sh
git clone https://github.com/mkttanabe/exif.git
gcc -fsanitize=address -ggdb -o exif_ASan sample_main.c exif.c
```

3. 修改 `config.ini`

自定义核心配置默认如下：
```ini
[generation]
mutation_ratio = 0.01 # 变异率
arithmetic_range = 0,35 # 字节随机范围，借鉴AFL: 0 < r <35
[evaluation]
round = 500 # fuzzing 多少轮
thread_count=5 # 线程数，请设置: cpu核数+1
```

此外，请将配置中的路径都改为自己的对应路径。

4. 开始 fuzzing

```sh
python src/main.py
```


# EXIF

Exif文件格式与JPEG文件格式相似，Exif会向JPEG中插入一些图像/数字信息以及缩略图信息，所以可以像查看JPEG文件一样，使用兼容JPEG的浏览器、图像查看器或者图像修改软件来查看Exif格式的图像文件。

`res/Canon_40D.jpg` 图片来自 [exif-samples](https://github.com/ianare/exif-samples/tree/master/jpg), 是一张正常的进行了 `Exif` 填充的 `JPEG` 图片。

根据规范：
- 图像开始标记： `0xFFD8` 
- 图像结尾标记： `0xFFD9` 
- APP1标记：`0xFFE1`
- 通用标记：`0xFFXX`

所有图像标记均以 `0xFF` 开头。

本实验并不想改变图像的长度或者文件类型，所以保持SOI和EOI标记完整不变。比如说，不会在图像的中间插入0xFFD9，因为这样会直接截断图像，使解析器工作异常。

查看图像信息：

```shell
# 图像信息 Exif
file res/Canon_40D.jpg
# 二进制 开头 0xFFD8，结尾 0xFFD9
hexdump res/Canon_40D.jpg 
# 哈希值
shasum res/Canon_40D.jpg 
```

# 待测程序

Program Under Test，后续采用 `PUT`  指代。

```sh
# 参考 https://fuzzing-project.org/tutorial2.html
git clone https://github.com/mkttanabe/exif.git
gcc -o exif sample_main.c exif.c
```

PUT 的使用方法如下：

```
./exif Canon_40D.jpg -verbose
```

# 预处理

典型的安全策略往往将 ` fatal signal` （例如段错误）视为违规测试，该策略易于实现，因为操作系统允许此类异常情况在没有任何检测的情况下被 fuzzer 捕获。

但该策略并不能检测所有的内存漏洞，例如堆栈缓冲区溢出，覆写了指针指向另一个有效地址，程序可能仅出现无效结果，而不会崩溃终止，因此 fuzzer 无法检测到该漏洞。

为了解决上述问题，需要采用一类被称为 `Sanitizers` 的工具，最早由谷歌发起，该类工具可以检测更多类型的错误：
  
- 内存类型安全
- 未定义行为
- 输入验证
- 语义差异

Google 的 Sanitizers 是开源工作集，包括了AddressSanitizer, MemorySanitizer, ThreadSanitizer, LeakSanitizer.

Sanitizers项目本是LLVM项目的一部分，GNU也将该系列工具加入到了自家的GCC编译器中，只需要编译时添加 `-fsanitize=address` 即可使用，为了方便调试，增加 `-ggdb`.

```sh
gcc -fsanitize=address -ggdb -o exif_ASan sample_main.c exif.c
```
此时得到了可执行文件 `exif_ASan`，后续实验都使用预处理后的 `exif_ASan`。


# 变异：生成测试样例

fuzzer 分为：
- generation-based fuzzer：基于生成，通过预定义模型、推理模型等生成测试用例
- mutation-based fuzzer：基于变异，常见的变异 seed 的方法有位翻转、算数突变、基于块的变异、基于字典的变异等

本次实验变异策略：
- 使用 `算数突变` 的变异方法，将文件转化为字节序列作为整数 `i` ，并对该值进行简单的算数运算 `i±r`，其中 `r` 由用户自定义配置，默认 `0<arithmetic_range<35`
- 结合 `位翻转` 的思路，提供变异比 `mutation_ratio`，仅对给变异比的字节进行突变

# 执行测试样例：评估

多线程使用生成的测试用例执行 PUT，本次实验将触发安全策略的测试用例保存到 `testcase` 中，未触发的将被删除。

`Triage` 用于分析和报告违反策略的安全用例，通分为：重复数据删除，优先级和测试用例最小化。

在本实验中，仅对输出结果做简单判断，并将 `Sanitizer` 的输出保存到 result 中，命名格式如下：
- HBO：heap buffer overflow
- SBO：stack buffer overflow
- ML：memory leaks
- SEGV：sigsegv(e.g. segmentation fault)

# 优化点

- 预处理阶段：Seed Selection、Seed Trimming
- 配置更新阶段：每次迭代后更新配置、维护种子池并且不断进化种子
- 白盒/灰盒测试：获取更多信息，如覆盖率

