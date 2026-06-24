"""Smoke tests for the Ableton project analyzer."""

from __future__ import annotations

import gzip
import tempfile
import unittest
from pathlib import Path

from .project_analyzer import AbletonProjectAnalyzer, render_markdown


MINIMAL_ABLETON_SET = """<?xml version="1.0" encoding="UTF-8"?>
<Ableton Creator="Ableton Live 12" MajorVersion="5" MinorVersion="12.0" Revision="test">
  <LiveSet>
    <Tempo><Manual Value="126" /></Tempo>
    <TimeSignature><Numerator Value="4" /><Denominator Value="4" /></TimeSignature>
    <Tracks>
      <MidiTrack Id="1">
        <Name><EffectiveName Value="Kick" /><UserName Value="Kick" /></Name>
        <ColorIndex Value="2" />
        <AutomationEnvelopes>
          <Envelopes>
            <AutomationEnvelope Id="0">
              <EnvelopeTarget><PointeeId Value="100" /></EnvelopeTarget>
              <Automation>
                <Events>
                  <FloatEvent Id="0" Time="-63072000" Value="0" />
                  <FloatEvent Id="1" Time="0" Value="0.5" />
                  <FloatEvent Id="2" Time="8" Value="1" />
                </Events>
              </Automation>
            </AutomationEnvelope>
          </Envelopes>
        </AutomationEnvelopes>
        <DeviceChain>
          <Mixer>
            <Speaker><Manual Value="true" /></Speaker>
            <SoloSink Value="false" />
            <Pan><Manual Value="0" /></Pan>
            <Volume><Manual Value="0.8" /><AutomationTarget Id="100" /></Volume>
            <Sends />
          </Mixer>
          <MainSequencer>
            <ClipTimeable>
              <ArrangerAutomation>
                <Events>
                  <MidiClip Id="1" Time="0">
                    <CurrentStart Value="0" />
                    <CurrentEnd Value="16" />
                    <Loop><LoopStart Value="0" /><LoopEnd Value="4" /><LoopOn Value="true" /></Loop>
                    <Name Value="Kick Pattern" />
                    <IsWarped Value="true" />
                    <Notes>
                      <KeyTracks>
                        <KeyTrack Id="0">
                          <MidiKey Value="60" />
                          <Notes>
                            <MidiNoteEvent Time="0" Duration="0.5" Velocity="100" IsEnabled="true" />
                            <MidiNoteEvent Time="1" Duration="0.5" Velocity="96" IsEnabled="true" />
                          </Notes>
                        </KeyTrack>
                      </KeyTracks>
                    </Notes>
                  </MidiClip>
                </Events>
              </ArrangerAutomation>
            </ClipTimeable>
          </MainSequencer>
          <DeviceChain>
            <Devices>
              <DrumRack Id="1"><UserName Value="Drum Rack" /><On><Manual Value="true" /></On></DrumRack>
            </Devices>
          </DeviceChain>
        </DeviceChain>
      </MidiTrack>
      <AudioTrack Id="2">
        <Name><EffectiveName Value="Noise Reverse" /><UserName Value="Noise Reverse" /></Name>
        <ColorIndex Value="3" />
        <AutomationEnvelopes><Envelopes /></AutomationEnvelopes>
        <DeviceChain>
          <Mixer>
            <Speaker><Manual Value="true" /></Speaker>
            <SoloSink Value="false" />
            <Pan><Manual Value="-0.25" /></Pan>
            <Volume><Manual Value="0.5" /></Volume>
            <Sends />
          </Mixer>
          <MainSequencer>
            <Sample>
              <ArrangerAutomation>
                <Events>
                  <AudioClip Id="2" Time="8">
                    <CurrentStart Value="8" />
                    <CurrentEnd Value="24" />
                    <Loop><LoopStart Value="0" /><LoopEnd Value="16" /><LoopOn Value="false" /></Loop>
                    <Name Value="" />
                    <IsWarped Value="true" />
                    <SampleRef><FileRef><Name Value="Noise Reverse.wav" /></FileRef></SampleRef>
                  </AudioClip>
                </Events>
              </ArrangerAutomation>
            </Sample>
          </MainSequencer>
          <DeviceChain><Devices><Eq8 Id="2"><On><Manual Value="true" /></On></Eq8></Devices></DeviceChain>
        </DeviceChain>
      </AudioTrack>
    </Tracks>
    <MasterTrack>
      <Name><EffectiveName Value="Master" /><UserName Value="Master" /></Name>
      <AutomationEnvelopes><Envelopes /></AutomationEnvelopes>
      <DeviceChain>
        <Mixer>
          <Speaker><Manual Value="true" /></Speaker>
          <SoloSink Value="false" />
          <Pan><Manual Value="0" /></Pan>
          <Volume><Manual Value="1" /></Volume>
          <Sends />
        </Mixer>
        <DeviceChain><Devices><Limiter Id="1"><UserName Value="Limiter" /><On><Manual Value="true" /></On></Limiter></Devices></DeviceChain>
      </DeviceChain>
    </MasterTrack>
    <Locators>
      <Locators>
        <Locator Id="0"><Time Value="16" /><Name Value="Drop" /></Locator>
      </Locators>
    </Locators>
  </LiveSet>
</Ableton>
"""


class AbletonProjectAnalyzerSmokeTest(unittest.TestCase):
    def _write_fixture(self, directory: Path) -> Path:
        fixture = directory / "minimal.als"
        with gzip.open(fixture, "wb") as fh:
            fh.write(MINIMAL_ABLETON_SET.encode("utf-8"))
        return fixture

    def test_analyzes_project_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            analysis = AbletonProjectAnalyzer(self._write_fixture(Path(tmp))).analyze()

        self.assertEqual(analysis["project"]["tempo_bpm"], 126.0)
        self.assertEqual(analysis["layers"]["track_count"], 3)
        self.assertEqual(analysis["layers"]["tracks_with_clips"], 2)
        self.assertEqual(analysis["arrangement"]["duration_bars"], 6.0)
        self.assertEqual(analysis["automation"]["envelope_count"], 1)

        layers = analysis["layers"]["by_layer"]
        self.assertIn("drums", layers)
        self.assertIn("fx", layers)
        self.assertGreater(layers["drums"]["midi_note_count"], 0)
        self.assertEqual(layers["fx"]["clip_count"], 1)

    def test_renders_markdown_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            analysis = AbletonProjectAnalyzer(self._write_fixture(Path(tmp))).analyze()

        markdown = render_markdown(analysis)

        self.assertIn("# Ableton Project Analysis", markdown)
        self.assertIn("## Arrangement", markdown)
        self.assertIn("## Mixing", markdown)
        self.assertIn("## Automation", markdown)


if __name__ == "__main__":
    unittest.main()
