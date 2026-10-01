from py4j.java_gateway import JavaGateway


class DataFrame:
    def __init__(self, jdf):
        self._jdf = jdf  # same attribute name as in PySpark

    def filter(self, op, value):
        return DataFrame(self._jdf.filter(op, value))

    def multiply(self, factor):
        return DataFrame(self._jdf.multiply(factor))

    def explain(self):
        print(self._jdf.explain())

    def count(self):
        return self._jdf.count()

    def collect(self):
        return list(self._jdf.collect())

    def count_by_mod(self, mod):
        return dict(self._jdf.countByMod(mod))


class SparkSession:
    def __init__(self):
        self._gateway = JavaGateway()
        self._jsession = self._gateway.entry_point

    def range(self, start, end):
        return DataFrame(self._jsession.range(start, end))


spark = SparkSession()
df = spark.range(0, 20).filter(">", 5).multiply(10).filter("<", 150)

df.explain()          # nothing has been executed yet
print(df.count())
print(df.collect())

print(spark.range(0, 20).filter(">", 5).count_by_mod(3))
