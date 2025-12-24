# inspect_aapl_csvs_no_missing_row.py
# -*- coding: utf-8 -*-

import json
from pathlib import Path
import pandas as pd
import numpy as np

FILES = {
    "futu_news": r"D:\GitHub\LocalFinData\data\news-futu-stock\AAPL.csv",
    "yahoo_news": r"D:\GitHub\LocalFinData\data\news-yh-stock\AAPL.csv",
    "local_price_data": r"D:\GitHub\LocalFinData\data\prices\AAPL.csv",
}

# 输出 JSON 文件
OUTPUT_JSON = r"D:\GitHub\LocalFinData\aapl_schema_snapshot.json"

DT_HINTS = ("date", "time", "datetime", "published", "scraped", "created", "updated", "at")


def is_null_like(v) -> bool:
    """识别 NaN/NaT/None/空字符串/仅空白"""
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except Exception:
        pass
    if isinstance(v, str) and v.strip() == "":
        return True
    return False


def infer_scalar_type(value, col_name: str | None = None) -> str:
    """对单个值做类型推断：null/bool/int/float/datetime/str/other"""
    if is_null_like(value):
        return "null"

    # numpy 标量转 python 标量
    if isinstance(value, (np.generic,)):
        value = value.item()

    if isinstance(value, (bool, np.bool_)):
        return "bool"

    if isinstance(value, (int, np.integer)) and not isinstance(value, bool):
        return "int"

    if isinstance(value, (float, np.floating)):
        return "float"

    if isinstance(value, pd.Timestamp):
        return "datetime"

    if isinstance(value, str):
        s = value.strip()
        low = s.lower()

        if low in ("true", "false"):
            return "bool"

        # int 尝试
        try:
            # 排除 1e3 这类科学计数法（int会失败，float能成功）
            if "e" not in low and "." not in low:
                int(s)
                return "int"
        except Exception:
            pass

        # float 尝试
        try:
            float(s)
            return "float"
        except Exception:
            pass

        # datetime 尝试：列名带时间提示更优先
        try_dt = True
        if col_name:
            if any(h in col_name.lower() for h in DT_HINTS):
                dt = pd.to_datetime(s, errors="coerce")
                if not pd.isna(dt):
                    return "datetime"
            else:
                # 没提示也试一次，但不强求
                dt = pd.to_datetime(s, errors="coerce", infer_datetime_format=True)
                if not pd.isna(dt):
                    return "datetime"
        elif try_dt:
            dt = pd.to_datetime(s, errors="coerce", infer_datetime_format=True)
            if not pd.isna(dt):
                return "datetime"

        return "str"

    return "other"


def find_first_complete_row(df: pd.DataFrame) -> tuple[int | None, dict | None]:
    """
    找到第一条“全列都非空”的行。
    返回 (row_index, row_dict)；若不存在返回 (None, None)
    """
    if df.shape[0] == 0:
        return None, None

    # 标准化：把纯空白字符串当作 NA
    # 注意：df 这里是 dtype=str 读入，空值可能是 NaN 或空串
    work = df.copy()

    # 将空白串统一为 NaN，便于 isna 判定
    for c in work.columns:
        work[c] = work[c].apply(lambda x: np.nan if (isinstance(x, str) and x.strip() == "") else x)

    # 找“全非空”的第一行
    mask_complete = work.notna().all(axis=1)
    idxs = np.flatnonzero(mask_complete.values)
    if len(idxs) == 0:
        return None, None

    i = int(idxs[0])
    return i, df.iloc[i].to_dict()


def analyze_csv(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"path": str(p), "error": "file_not_found"}

    try:
        # dtype=str：尽量保留原始文本；keep_default_na=True：识别 NA/NaN
        df = pd.read_csv(p, dtype=str, keep_default_na=True)
    except Exception as e:
        return {"path": str(p), "error": f"read_csv_failed: {e}"}

    columns = list(df.columns)
    rows, cols = int(df.shape[0]), int(df.shape[1])

    if rows == 0:
        return {
            "path": str(p),
            "columns": columns,
            "sample_row_index": None,
            "sample_row": None,
            "column_types": {c: "null" for c in columns},
            "rows": 0,
            "cols": cols,
            "note": "empty_file",
        }

    sample_idx, sample_row = find_first_complete_row(df)

    if sample_row is None:
        # 没有任何“全非空”行
        return {
            "path": str(p),
            "columns": columns,
            "sample_row_index": None,
            "sample_row": None,
            "column_types": {c: "unknown" for c in columns},
            "rows": rows,
            "cols": cols,
            "note": "no_row_without_missing_values",
        }

    # 用“完整样本行”做类型推断（每列一定有值，不会被 NaN 干扰）
    col_types = {c: infer_scalar_type(sample_row.get(c), c) for c in columns}

    return {
        "path": str(p),
        "columns": columns,
        "sample_row_index": int(sample_idx),
        "sample_row": sample_row,
        "column_types": col_types,
        "rows": rows,
        "cols": cols,
        "note": "sample_row_is_first_row_with_no_missing_values",
    }


def main():
    result = {"sources": {}}
    for source_name, file_path in FILES.items():
        result["sources"][source_name] = analyze_csv(file_path)

    out_path = Path(OUTPUT_JSON)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved JSON -> {out_path}")


if __name__ == "__main__":
    main()
