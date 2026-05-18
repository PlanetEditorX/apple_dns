import json

APPLE_FILE = ROOT / "data/apple_fixed_domains.txt"
AD_FILE = ROOT / "data/ad_domains.txt"
HEADER_FILE = ROOT / "templates/header.xml"
FOOTER_FILE = ROOT / "templates/footer.xml"
OUTPUT_FILE = ROOT / "output/dns.mobileconfig"


def read_domains(file_path):
    if not file_path.exists():
        return set()

    return {
        line.strip()
        for line in file_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


# GitHub Actions 输入 JSON
json_input = Path("input.json").read_text(encoding="utf-8")

payload = json.loads(json_input)

new_domains = set()

for item in payload.get("items", []):
    domain = item.get("request", {}).get("domain")

    if domain:
        new_domains.add(domain.lower())


apple_domains = read_domains(APPLE_FILE)
old_ad_domains = read_domains(AD_FILE)

all_ad_domains = sorted(old_ad_domains | new_domains)

# 保存广告域名
AD_FILE.write_text(
    "\n".join(all_ad_domains) + "\n",
    encoding="utf-8"
)

# 合并所有域名
final_domains = sorted(apple_domains | set(all_ad_domains))

# 生成 XML
xml_domains = "\n".join(
    f"                    <string>{d}</string>"
    for d in final_domains
)

header = HEADER_FILE.read_text(encoding="utf-8")
footer = FOOTER_FILE.read_text(encoding="utf-8")

final_xml = header + "\n" + xml_domains + "\n" + footer

OUTPUT_FILE.write_text(final_xml, encoding="utf-8")

print(f"生成完成，共 {len(final_domains)} 个域名")