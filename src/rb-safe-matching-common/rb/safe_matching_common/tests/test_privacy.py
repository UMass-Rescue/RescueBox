from rb.safe_matching_common.privacy import redact_text


def test_redact_text_removes_name_email_phone_and_place():
    text = "John Smith emailed john@x.com from Boston, call 413-555-0100"
    redacted = redact_text(text)
    for leaked in ("John Smith", "john@x.com", "Boston", "413-555-0100"):
        assert leaked not in redacted
    for tag in ("<PERSON>", "<EMAIL_ADDRESS>", "<LOCATION>", "<PHONE_NUMBER>"):
        assert tag in redacted
