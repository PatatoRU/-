from pathlib import Path


def test_stub_provider_files_removed():
    assert not Path("app/providers/yandex_provider.py").exists()
    assert not Path("app/providers/twogis_provider.py").exists()
    assert not Path("app/providers/tripadvisor_provider.py").exists()
