# Prompt/schema 回归对照

这个离线工具把两个版本的抽取结果放到**同一份冻结数据集**上评分。它不调用模型，不判断语义相似，也不把格式通过当成内容正确。仓库里的 before/after 文件是合成样例，不是真实模型实验。

从仓库根目录运行：

```bash
python3 -m unittest discover -s examples/prompt-regression/tests -v
python3 examples/prompt-regression/compare.py \
  --dataset examples/prompt-regression/dataset.json \
  --before examples/prompt-regression/results-before.json \
  --after examples/prompt-regression/results-after.json
```

每份运行结果必须带 `dataset_version`、`dataset_sha256`、`prompt_version` 和每个 case 的一条记录。先对规范化后的 dataset JSON（UTF-8、键排序、紧凑分隔符、保留 Unicode）算 SHA-256，再写入两份结果；CLI 会核对散列。失败调用也要保留为 `status: error`，仍留在分母中。重复/漏失 case、重复 JSON key、dataset 版本或散列不一致都会拒绝评分。

报告分别给出结构成功率、逐字段精确率、全字段 exact-match、失败次数、总体退化 case 与逐字段退化 case。比较只对字符串做 NFC 与首尾空白归一，再精确相等比较；如果领域需要大小写、货币或日期归一化，应先写出并版本化规则，不要临时“清洗”结果来让分数好看。

真实模型实验还要把模型/provider 版本、请求参数、prompt/schema hash、运行时间、每次 usage 和错误原因保存在结果产物中。该脚本只核验数据集身份和评分契约；它不能证明 run 文件确实来自所声明模型，也不能证明人工 rubric 的语义正确性。对外宣称 prompt 改进前，应检查回归 case、预先定义目标指标，并在独立留出集复核。
