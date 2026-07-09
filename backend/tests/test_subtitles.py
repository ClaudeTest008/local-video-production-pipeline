from app.modules.subtitles.service import to_srt, to_vtt

SEGMENTS = [
    {"start": 0.0, "end": 2.5, "text": "Hello world"},
    {"start": 2.5, "end": 3661.25, "text": "Second line"},
]


def test_srt_format():
    srt = to_srt(SEGMENTS)
    assert "1\n00:00:00,000 --> 00:00:02,500\nHello world" in srt
    assert "2\n00:00:02,500 --> 01:01:01,250\nSecond line" in srt


def test_vtt_format():
    vtt = to_vtt(SEGMENTS)
    assert vtt.startswith("WEBVTT\n\n")
    assert "00:00:00.000 --> 00:00:02.500\nHello world" in vtt


def test_track_crud_and_export(client, project):
    track = client.post(
        "/api/subtitles", json={"project_id": project["id"], "segments": SEGMENTS}
    ).json()

    srt = client.get(f"/api/subtitles/{track['id']}/export", params={"fmt": "srt"})
    assert srt.status_code == 200 and "Hello world" in srt.text

    vtt = client.get(f"/api/subtitles/{track['id']}/export", params={"fmt": "vtt"})
    assert vtt.text.startswith("WEBVTT")

    assert client.delete(f"/api/subtitles/{track['id']}").status_code == 204


def test_transcribe_needs_extra(client, project):
    resp = client.post(
        "/api/subtitles/transcribe", json={"project_id": project["id"], "audio_path": "x.wav"}
    )
    assert resp.status_code in (201, 501)  # 501 without the optional extra installed
