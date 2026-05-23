import pytest
from translators.dummy_translator import DummyTranslator

def test_dummy_translator_modes():
    # 測試 same 模式
    trans_same = DummyTranslator(mode="same")
    text = "Hello world of academic PDFs."
    res_same = trans_same.translate(text)
    assert res_same == f"[Same: {text}]"

    # 測試 short 模式
    trans_short = DummyTranslator(mode="short")
    res_short = trans_short.translate(text)
    assert "短譯文" in res_short

    # 測試 normal 模式
    trans_normal = DummyTranslator(mode="normal")
    res_normal = trans_normal.translate(text)
    # normal 應該會產生合理的中文句子，其長度不為空
    assert len(res_normal) > 5

    # 測試 long 模式
    trans_long = DummyTranslator(mode="long")
    res_long = trans_long.translate(text)
    assert len(res_long) > len(res_normal)

    # 測試 stress 模式
    trans_stress = DummyTranslator(mode="stress")
    res_stress = trans_stress.translate(text)
    assert "壓測" in res_stress
    assert len(res_stress) > len(res_long)
