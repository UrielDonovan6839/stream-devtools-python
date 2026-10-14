from types import SimpleNamespace

from src.devtools_stream import StreamRequest, stream_tool_events


def sdk_chunk(text: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=text))]
    )


def test_stream_marks_release_ready_after_assembling_model_text():
    events = list(
        stream_tool_events(
            StreamRequest(prompt="inspect build", release="r42"),
            chunks=[sdk_chunk("green "), sdk_chunk("tests")],
        )
    )

    assert [event.kind for event in events] == [
        "build",
        "build",
        "build",
        "diagnostic",
        "release",
    ]
    assert events[-2].message == "assembled 11 response characters"
    assert events[-1].message == "r42 ready"
