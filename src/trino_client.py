import trino
import pandas as pd


def get_connection(
    host,
    port,
    user,
    catalog,
    schema,
):
    return trino.dbapi.connect(
        host=host,
        port=port,
        user=user,
        catalog=catalog,
        schema=schema,
    )


def read_sql(
    sql,
    connection,
):
    return pd.read_sql(sql, connection)