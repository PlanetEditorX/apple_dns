import json
from pathlib import Path

# 根目录
ROOT = Path(__file__).resolve().parent.parent

# 文件路径
APPLE_FILE = ROOT / "data/apple_fixed_domains.txt"  # 固定 Apple 域名
AD_FILE = ROOT / "data/ad_domains.txt"              # 历史广告域名
HEADER_FILE = ROOT / "templates/header.xml"        # XML 头
FOOTER_FILE = ROOT / "templates/footer.xml"        # XML 尾
OUTPUT_FILE = ROOT / "output/dns.mobileconfig"     # 输出文件
INPUT_JSON = ROOT / "input.json"                   # workflow JSON
INPUT_DOMAINS = ROOT / "input_domains.txt"        # 手动域名输入

# 确保输出目录存在
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

def read_domains(path):
    """读取域名文件，去除注释、空行"""
    if not path.exists():
        return set()
    domains = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("<!--"):
            continue
        # 兼容 XML string 标签
        line = line.replace("<string>", "").replace("</string>", "").strip()
        if line:
            domains.add(line.lower())
    return domains

# ----------- 读取各类域名 ------------

# 1. 固定 Apple 域名
apple_domains = read_domains(APPLE_FILE)

# 2. 历史广告域名
old_ad_domains = read_domains(AD_FILE)

# 3. JSON 输入域名
new_domains = set()
if INPUT_JSON.exists():
    payload_text = INPUT_JSON.read_text(encoding="utf-8").strip()
    if payload_text:
        try:
            payload = json.loads(payload_text)
            for item in payload.get("items", []):
                domain = item.get("request", {}).get("domain")
                if domain:
                    new_domains.add(domain.lower())
        except json.JSONDecodeError:
            print("⚠️ JSON 解析失败，忽略 JSON 输入")

# 4. 手动输入域名
manual_domains = set()
if INPUT_DOMAINS.exists():
    content = INPUT_DOMAINS.read_text(encoding="utf-8")
    # 支持：换行、空格、逗号、中文逗号
    content = (
        content
        .replace(",", " ")
        .replace("，", " ")
    )
    for line in content.splitlines():
        for part in line.split():
            domain = part.strip().lower()
            if not domain:
                continue
            manual_domains.add(domain)

# ----------- 合并去重 ------------
all_ad_domains = sorted(old_ad_domains | new_domains | manual_domains)

# 保存广告域名到 ad_domains.txt
AD_FILE.write_text("\n".join(all_ad_domains) + "\n", encoding="utf-8")

# 最终所有域名（Apple + 广告/追踪域名）
final_domains = sorted(apple_domains | set(all_ad_domains))

# 生成 XML <string> 标签
xml_domains = "\n".join(f"                    <string>{d}</string>" for d in final_domains)

# 读取模板
header = HEADER_FILE.read_text(encoding="utf-8")
footer = FOOTER_FILE.read_text(encoding="utf-8")

# 拼接最终 XML
final_xml = header + "\n" + xml_domains + "\n" + footer

# 写入输出文件
OUTPUT_FILE.write_text(final_xml, encoding="utf-8")

print(f"✅ 生成完成，共 {len(final_domains)} 个域名")
print(f"输出文件: {OUTPUT_FILE}")