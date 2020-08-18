from google.cloud import speech_v1p1beta1
import io
import os
from io import StringIO


def sample_transcribe(newfile_name, object_uri, bucket):
    """
    Args:
      transcription file name
      Google Cloud URI of uploaded sound file
      Firebase storage bucket
    """

    client = speech_v1p1beta1.SpeechClient()

        # When enabled, the first result returned by the API will include a list
        # of words and the confidence level for each of those words.
    enable_word_confidence = True

        # If enabled, each word in the first alternative of each result will be
        # tagged with a speaker tag to identify the speaker.
    enable_speaker_diarization = True
    enable_wordtime_offsets = True

        # The language of the supplied audio
    language_code = "en-US"
    config = {
        "enable_speaker_diarization": enable_speaker_diarization,
        "enable_word_confidence": enable_word_confidence,
        "language_code": language_code,
        #"enableWordTimeOffsets": enable_wordtime_offsets,
    }
    # file_to_open = local_directory + "/" + local_file_name
    # with io.open(file_to_open, "rb") as f:
    #    content = f.read()

    # call out to Google speech-to-text
    audio = {"uri": object_uri}
    operation = client.long_running_recognize(config, audio)

    print(u"Waiting for operation to complete...")
    # set timeout to 4 hours, for now...
    response = operation.result(timeout=14400)

    # concatenate transcript into string bufer
    soutput = StringIO()
    for i in range(0, response.results.__len__()-1):
        alternative = response.results[i].alternatives[0]
        soutput.write(alternative.transcript + '\n')
    
    transcriptionBlob = bucket.blob(newfile_name)  # name of file in firebase
    transcriptionBlob.upload_from_string(soutput.getvalue()) # do upload to the cloud
    
    return (transcriptionBlob)
