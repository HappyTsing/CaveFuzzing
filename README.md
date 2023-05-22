# CaveFuzzing

Fuzzing Like A Caveman 系列教程的练手代码。

# Usage

```
pipenv install
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
```

# Bit-Flipping

fuzzer 分为：
- generation-based fuzzer：基于生成，通过预定义模型、推理模型等生成测试用例
- mutation-based fuzzer：基于变异，常见的变异 seed 的方法有位翻转、算数突变、基于块的变异、基于字典的变异等

本次实验结合使用 `算数突变` 的变异方法，将文件转化为字节序列作为整数 `i` ，并对该值进行简单的算数运算 `i±r`，其中 `r` 由用户自定义配置，默认 $0<arithmetic_range<35$。同时结合 `位翻转` 的思路，提供变异比 `mutation_ratio`，仅对给变异比的字节进行突变。
