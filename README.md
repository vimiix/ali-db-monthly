# 阿里数据库月报 Wapper

## 部署

> 首次启动如果数据库中没有数据会全量抓取文件链接，所以需要等待一段时间后，页面才可以看到数据，后续启动增量爬取

```shell
cp src/config.ini.sample src/config.ini
vim src/config.ini # 修改配置

pipenv install --python `python3 -c "import platform;print(platform.python_version())"`
pipenv run python src/main.py
```

## 预览

- [alidbmonthly.vimiix.com](https://alidbmonthly.vimiix.com)

![preview.png](./static/preview.png)
