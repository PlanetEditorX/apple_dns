import json
import uuid
from pathlib import Path

# -----------------------------
# 配置固定文件路径
# -----------------------------
APPLE_BLOCK_FILE = "apple_fixed_domains.xml"   # 固定的苹果屏蔽域名列表
AD_BLOCK_FILE = "ad_domains.xml"              # 用户新增 JSON 提取的广告域名列表
OUTPUT_PLIST_FILE = "dns_block_profile.plist"  # 最终生成的描述文件

# -----------------------------
# 读取固定苹果域名
# -----------------------------
def read_apple_domains(file_path):
    if not Path(file_path).exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # 提取 <string>...</string> 内容
    domains = [line.strip().replace("<string>", "").replace("</string>", "")
               for line in lines if "<string>" in line]
    return domains

# -----------------------------
# 读取用户 JSON 并提取域名
# -----------------------------
def extract_domains_from_json(json_input):
    data = json.loads(json_input)
    domains = set()
    for item in data.get("items", []):
        domain = item.get("request", {}).get("domain")
        if domain:
            domains.add(domain)
    return sorted(domains)

# -----------------------------
# 生成广告域名 XML
# -----------------------------
def write_ad_domains(domains, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        for domain in domains:
            f.write(f'        <string>{domain}</string>\n')

# -----------------------------
# 生成最终 plist
# -----------------------------
def generate_plist(apple_domains, ad_domains, output_file):
    supplemental_domains = apple_domains + ad_domains
    supplemental_xml = "\n".join([f'                    <string>{d}</string>' for d in supplemental_domains])

    plist_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>
        <dict>
            <key>DNSSettings</key>
            <dict>
                <key>DNSProtocol</key>
                <string>HTTPS</string>
                <key>ServerURL</key>
                <string>https://127.0.0.1/dns-query</string>
                <key>SupplementalMatchDomains</key>
                <array>
{supplemental_xml}
                </array>
                <key>SupplementalMatchDomainsNoSearch</key>
                <true/>
            </dict>
            <key>PayloadDescription</key>
            <string>通过本地 DoH 服务屏蔽 Apple 系统更新域名及各类广告/追踪域名，实现设备免打扰。</string>
            <key>PayloadDisplayName</key>
            <string>屏蔽系统更新及广告追踪</string>
            <key>PayloadIdentifier</key>
            <string>com.example.doh.antirefresh.ads.dns</string>
            <key>PayloadType</key>
            <string>com.apple.dnsSettings.managed</string>
            <key>PayloadUUID</key>
            <string>{uuid.uuid4()}</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
        </dict>
    </array>
    <key>PayloadDescription</key>
    <string>安装此描述文件后，所有列出的 Apple 更新域名及广告追踪域名都将通过本地 DoH 服务器解析（通常解析到 0.0.0.0），从而有效阻止 iOS 系统更新检测并减少广告骚扰。</string>
    <key>PayloadDisplayName</key>
    <string>屏蔽系统更新及广告追踪</string>
    <key>PayloadIdentifier</key>
    <string>com.example.doh.antirefresh.ads.v1</string>
    <key>PayloadScope</key>
    <string>System</string>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadUUID</key>
    <string>{uuid.uuid4()}</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>
"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(plist_template)
    print(f"生成完成: {output_file}")

# -----------------------------
# 主流程
# -----------------------------
if __name__ == "__main__":
    # 读取固定苹果域名
    apple_domains = read_apple_domains(APPLE_BLOCK_FILE)

    # 输入手动 JSON（这里可以改成从文件读取）
    json_input = input("请输入 JSON 数据:\n")
    ad_domains = extract_domains_from_json(json_input)

    # 去重、排序（合并固定和新增域名时再排序）
    ad_domains = sorted(set(ad_domains))

    # 保存广告域名到文件
    write_ad_domains(ad_domains, AD_BLOCK_FILE)

    # 生成最终 plist
    generate_plist(apple_domains, ad_domains, OUTPUT_PLIST_FILE)