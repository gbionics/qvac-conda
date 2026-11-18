import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("update", Path(__file__).resolve().parents[1] / "scripts/update_prebuilt.py")
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


def release(version="0.24.0"):
    names = [f"tetherto_qvac_sdk-{version}-py3-none-{tag}.whl" for tag in (
        "manylinux_2_35_x86_64", "manylinux_2_35_aarch64", "macosx_13_0_arm64", "win_amd64"
    )]
    return {
        "tag_name": f"sdk-v{version}", "draft": False, "prerelease": False,
        "assets": [{"name": name, "digest": "sha256:" + "a" * 64,
                    "browser_download_url": f"https://github.com/tetherto/qvac/releases/download/sdk-v{version}/{name}"} for name in names],
    }


class UpdateTests(unittest.TestCase):
    def test_selects_highest_stable_sdk_without_downgrading(self):
        draft = {**release("10.0.0"), "draft": True}
        pre = {**release("11.0.0"), "prerelease": True}
        other = {**release("12.0.0"), "tag_name": "other-v12.0.0"}
        items = [release("0.9.0"), release("0.24.0"), draft, pre, other]
        self.assertEqual(update.latest_release(items, "0.23.0")["tag_name"], "sdk-v0.24.0")
        self.assertIsNone(update.latest_release(items, "0.24.0"))
        self.assertIsNone(update.latest_release(items, "0.25.0"))

    def test_atomic_update_includes_os_floor_and_resets_build(self):
        original = update.RECIPE.read_text().replace("build_number: 0", "build_number: 7")
        candidate = update.updated_recipe(original, release())
        self.assertIn('minimum_osx: "13.0"', candidate)
        self.assertIn('minimum_glibc: "2.35"', candidate)
        self.assertIn("build_number: 0", candidate)
        self.assertNotIn("0.23.0", candidate)
        self.assertEqual(candidate.split("  # END RELEASE")[1], original.split("  # END RELEASE")[1])

    def test_missing_or_duplicate_platform_fails(self):
        for duplicate in [False, True]:
            item = release()
            if duplicate:
                item["assets"].append(copy.deepcopy(item["assets"][0]))
            else:
                item["assets"].pop()
            with self.assertRaises(ValueError):
                update.updated_recipe(update.RECIPE.read_text(), item)

    def test_unexpected_asset_url_fails(self):
        item = release()
        item["assets"][0]["browser_download_url"] = "https://example.com/untrusted.whl"
        with self.assertRaises(ValueError):
            update.release_context(item)

    def test_mismatched_linux_minimum_fails(self):
        item = release()
        asset = item["assets"][1]
        for key in ["name", "browser_download_url"]:
            asset[key] = asset[key].replace("manylinux_2_35", "manylinux_2_36")
        with self.assertRaises(ValueError):
            update.release_context(item)


if __name__ == "__main__":
    unittest.main()
