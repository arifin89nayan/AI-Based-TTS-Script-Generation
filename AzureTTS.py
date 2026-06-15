"""
Azure synthesis (diagram steps 12 -> 13): SSML in, MP3 file out.
Import of the SDK is done lazily so the rest of the pipeline (and tests)
work without Azure installed.
"""


def synthesize(ssml: str, out_path: str, key: str, region: str, audio_format: str) -> str:
    import azure.cognitiveservices.speech as speechsdk

    if not key or not region:
        raise RuntimeError(
            "AZURE_SPEECH_KEY and AZURE_SPEECH_REGION must be set in the environment."
        )

    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.set_speech_synthesis_output_format(
        getattr(speechsdk.SpeechSynthesisOutputFormat, audio_format)
    )
    audio_config = speechsdk.audio.AudioOutputConfig(filename=out_path)
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )

    result = synthesizer.speak_ssml_async(ssml).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = speechsdk.SpeechSynthesisCancellationDetails(result)
        raise RuntimeError(
            f"Azure synthesis failed: {result.reason}\n"
            f"  Error code   : {details.error_code}\n"
            f"  Error details: {details.error_details}"
        )
    return out_path