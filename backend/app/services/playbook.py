"""Sector-specific mitigation playbooks (template + optional LLM polish)."""

from __future__ import annotations

from app.schemas import Industry, PlaybookItem, PlaybookResponse

_TEMPLATES: dict[str, list[PlaybookItem]] = {
    "default": [
        PlaybookItem(
            title="Contain affected hosts",
            action="Isolate endpoints at the network layer; preserve volatile memory if ransomware is suspected.",
            sample_query='index=edr host="WORKSTATION*" AND (parent_process="WINWORD.EXE" OR process="powershell.exe")',
        ),
        PlaybookItem(
            title="Credential rotation",
            action="Force password reset for impacted accounts; revoke sessions and refresh tokens.",
            sample_query="index=iam OR index=auth user=* action=login OR action=MFA*",
        ),
        PlaybookItem(
            title="Threat intel enrichment",
            action="Pivot on IPs, domains, and hashes in your TI platform; block at perimeter.",
            sample_query='index=proxy OR index=dns dest IN ("*")',
        ),
    ],
    "healthcare": [
        PlaybookItem(
            title="PHI access review",
            action="Validate bulk exports against approved workflows; notify privacy officer if unapproved.",
            sample_query='index=ehr action=bulk_export OR "patient_mrn"',
        ),
        PlaybookItem(
            title="Clinical workstation containment",
            action="Segment VLANs for clinical devices; block nonessential outbound from EHR subnets.",
            sample_query="index=firewall src_net=CLINICAL_VLAN dest_net=INTERNET",
        ),
    ],
    "finance": [
        PlaybookItem(
            title="Fraud & SWIFT monitoring",
            action="Correlate new-device logins with wire initiation; step-up authentication.",
            sample_query='index=auth app=swift* OR index=wire (result=success OR result=failure)',
        ),
        PlaybookItem(
            title="MFA abuse detection",
            action="Alert on rapid MFA prompts; consider FIDO2 enforcement for privileged roles.",
            sample_query="index=mfa action=prompt_sent | stats count by user | where count > 4",
        ),
    ],
    "manufacturing": [
        PlaybookItem(
            title="OT boundary enforcement",
            action="Block RDP from non-corporate ASNs to engineering jump hosts.",
            sample_query="index=vpn OR index=rdp dest_segment=OT_JUMP",
        ),
    ],
    "energy": [
        PlaybookItem(
            title="Engineering change validation",
            action="Verify Modbus/SCADA writes against maintenance windows and digital work permits.",
            sample_query='index=scada protocol=modbus action=WRITE* NOT maint_window=true',
        ),
    ],
    "government": [
        PlaybookItem(
            title="Credential dumping response",
            action="Treat LSASS access from non-system tools as incident priority; hunt for lateral movement.",
            sample_query='index=sysmon EventID=10 TargetImage="*lsass.exe"',
        ),
    ],
    "cloud": [
        PlaybookItem(
            title="IAM blast radius",
            action="Revert inline policies; enable CloudTrail integrity monitoring and MFA on break-glass.",
            sample_query='eventSource="iam.amazonaws.com" eventName="PutUserPolicy"',
        ),
    ],
}


def build_playbook(industry: Industry, extra_note: str | None = None) -> PlaybookResponse:
    sector = industry
    items = list(_TEMPLATES.get(sector, _TEMPLATES["default"]))
    if sector != "default":
        items = items + _TEMPLATES["default"][:1]
    return PlaybookResponse(sector=sector, items=items[:6], notes=extra_note)
