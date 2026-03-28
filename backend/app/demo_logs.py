"""Curated demo logs (diverse formats; inspired by public SIEM-style corpora)."""

from app.schemas import DemoLogEntry

DEMO_LOGS: list[DemoLogEntry] = [
    DemoLogEntry(
        id="demo-ransomware-cef",
        title="Ransomware — CEF lateral movement",
        category="ransomware",
        raw_log=(
            "CEF:0|SecurityVendor|EDR|12.0|1002|Suspicious PowerShell|10|"
            "src=10.20.30.40 suser=DOMAIN\\jsmith "
            "fname=C:\\\\Windows\\\\Temp\\\\enc.ps1 "
            "msg=Encoded PowerShell spawned from WINWORD.EXE "
            "externalId=evt-88421 deviceHostName=WS-HR-044"
        ),
        expected_severity="critical",
        mitre_hint=["T1059", "T1486", "T1021"],
    ),
    DemoLogEntry(
        id="demo-ransomware-rundll32",
        title="Ransomware — rundll32 LOLBin from Office (suspicious DLL)",
        category="ransomware",
        raw_log=(
            'EventID=1 RuleName=ProcessCreate Image="C:\\Windows\\System32\\rundll32.exe" '
            'CommandLine="rundll32.exe shell32.dll,Control_RunDLL '
            'C:\\Users\\Public\\AppData\\stage\\payloader.dll,DllRegisterServer" '
            'ParentImage="C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE" '
            'User=ACME\\jsmith IntegrityLevel=Medium'
        ),
        expected_severity="critical",
        mitre_hint=["T1218", "T1486", "T1566"],
    ),
    DemoLogEntry(
        id="demo-iot-brute",
        title="IoT — repeated SSH failures (Syslog)",
        category="iot",
        raw_log=(
            "<134>1 2024-11-02T14:22:01Z camera-fw01 sshd[4412]: "
            "Failed password for root from 203.0.113.77 port 54221 ssh2"
        ),
        expected_severity="medium",
        mitre_hint=["T1110", "T1078"],
    ),
    DemoLogEntry(
        id="demo-health-phi",
        title="Healthcare — unusual EHR access",
        category="healthcare",
        raw_log=(
            '{"timestamp":"2024-11-03T09:15:22Z","event":"ehr_access",'
            '"user":"nurse_kim","patient_mrn":"MRN-77821","action":"bulk_export",'
            '"records":4200,"source_ip":"198.51.100.22","user_agent":"curl/7.81.0"}'
        ),
        expected_severity="high",
        mitre_hint=["T1530", "T1078"],
    ),
    DemoLogEntry(
        id="demo-finance-phish",
        title="Finance — suspicious login + MFA fatigue",
        category="finance",
        raw_log=(
            "2024-11-04 08:01:33 SWIFT-GW authd: user=swift_ops "
            "action=login result=success src=192.0.2.15 geo=Unknown "
            "mfa=prompt_sent x5_within_60s=true device_id=new"
        ),
        expected_severity="high",
        mitre_hint=["T1078", "T1621"],
    ),
    DemoLogEntry(
        id="demo-energy-scada",
        title="Energy — Modbus write outside maintenance window",
        category="energy",
        raw_log=(
            "SCADA|PLC-BAY3|MODBUS|WRITE_HOLDING|"
            "register=40001 value=0xffff src=10.55.1.9 "
            "engineer_session=false maint_window=false"
        ),
        expected_severity="critical",
        mitre_hint=["T0855", "T0806"],
    ),
    DemoLogEntry(
        id="demo-gov-cred-dump",
        title="Government — LSASS access attempt",
        category="government",
        raw_log=(
            "WinEvt:Security EID=4656 Object=\\\\Device\\\\HarddiskVolume3\\\\"
            "Windows\\\\System32\\\\lsass.exe "
            "SubjectUserName=svc_backup AccessMask=0x1fffff "
            "ProcessName=C:\\\\Tools\\\\procdump64.exe IPAddress=-"
        ),
        expected_severity="high",
        mitre_hint=["T1003", "T1059"],
    ),
    DemoLogEntry(
        id="demo-cloud-iam",
        title="Cloud — IAM policy tampering",
        category="cloud",
        raw_log=(
            '{"eventVersion":"1.08","eventTime":"2024-11-05T16:40:12Z",'
            '"eventSource":"iam.amazonaws.com","eventName":"PutUserPolicy",'
            '"userIdentity":{"type":"IAMUser","userName":"breakglass_old"},'
            '"sourceIPAddress":"203.0.113.10","requestParameters":'
            '{"userName":"breakglass_old","policyName":"AdminLike"}}'
        ),
        expected_severity="critical",
        mitre_hint=["T1098", "T1078"],
    ),
    DemoLogEntry(
        id="demo-malware-c2",
        title="Malware — DNS beaconing",
        category="malware",
        raw_log=(
            "dns-query|host=wksta-17|qname=cdn-upd.badsite.xyz|"
            "qtype=A|rcode=NOERROR|answers=1|ttl=60|"
            "interval_pattern=300s_jitter_low"
        ),
        expected_severity="medium",
        mitre_hint=["T1071", "T1568"],
    ),
    DemoLogEntry(
        id="demo-mfg-plc",
        title="Manufacturing — engineering workstation RDP",
        category="manufacturing",
        raw_log=(
            "CEF:0|CorpSIEM|VPN|3.2|9001|RDP Session|5|"
            "src=185.220.101.44 dst=10.12.0.5 duser=ENG\\\\plc_admin "
            "reason=Successful RDP from non-corporate ASN"
        ),
        expected_severity="high",
        mitre_hint=["T1021", "T1078"],
    ),
    DemoLogEntry(
        id="demo-batch-nlp-lab",
        title="Batch NLP lab — TF-IDF similarity + Isolation Forest",
        category="lab",
        raw_log=(
            "<134>1 2024-11-10T10:00:01Z edge01 sshd[8812]: Failed password for root from 203.0.113.10 port 54201 ssh2\n"
            "<134>1 2024-11-10T10:00:03Z edge01 sshd[8814]: Failed password for root from 203.0.113.11 port 54222 ssh2\n"
            "<134>1 2024-11-10T10:00:05Z edge01 sshd[8816]: Failed password for root from 203.0.113.12 port 54199 ssh2\n"
            "<134>1 2024-11-10T10:00:07Z edge01 sshd[8818]: Failed password for invalid user admin from 203.0.113.10 port 54300 ssh2\n"
            "dns-query|host=wksta-44|qname=stager.pastebin-analog.test|qtype=TXT|rcode=NOERROR|c2_candidate=true\n"
            "2024-11-10 10:00:25 HOST=DC01 SERVICE=wsus ACTION=approved_updates_installed kb=5032198 reboot_pending=false"
        ),
        expected_severity="high",
        mitre_hint=["T1110", "T1071"],
    ),
    DemoLogEntry(
        id="demo-benign-patch",
        title="Benign — scheduled patching (baseline)",
        category="baseline",
        raw_log=(
            "2024-11-06 02:00:01 HOST=DC01 SERVICE=wsus "
            "ACTION=approved_updates_installed kb=5032198 reboot_pending=false"
        ),
        expected_severity="info",
        mitre_hint=[],
    ),
]


def get_demo_logs() -> list[DemoLogEntry]:
    return DEMO_LOGS
