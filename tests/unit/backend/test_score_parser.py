from backend.services.scores.parser import parse_musicxml


def test_parse_musicxml_returns_canonical_summary_for_valid_fixture():
    result = parse_musicxml(
        b"""
        <score-partwise version="4.0">
          <work><work-title>Etude in C</work-title></work>
          <part-list>
            <score-part id="P1"><part-name>Clarinet</part-name></score-part>
          </part-list>
          <part id="P1">
            <measure number="1">
              <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration></note>
              <note><rest/><duration>4</duration></note>
            </measure>
          </part>
        </score-partwise>
        """
    )

    assert result.failure is None
    assert result.canonical_score is not None
    assert result.canonical_score.schema_version == "v1"
    assert result.canonical_score.title == "Etude in C"
    assert result.canonical_score.parts == [{"id": "P1", "name": "Clarinet"}]
    assert result.canonical_score.measure_count == 1
    assert result.canonical_score.note_count == 1
    assert result.canonical_score.rest_count == 1


def test_parse_musicxml_maps_invalid_xml_to_typed_failure():
    result = parse_musicxml(b"<score-partwise><part-list>")

    assert result.canonical_score is None
    assert result.failure is not None
    assert result.failure.failure_type.value == "invalid_xml"
