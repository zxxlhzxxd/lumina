import { useEffect, useRef, useState } from "react";
import { Alert } from "antd";
import { mediaUrl } from "../api";
import type { PlayMode } from "../types";

interface Props {
  projectId: string | null;
  audioRef: string;
  playMode: PlayMode;
}

const LOAD_ERROR_MESSAGE = "音频加载失败，请检查文件是否存在，或重新选择音频。";

function releaseAudio(audio: HTMLAudioElement | null) {
  if (!audio) return;
  audio.pause();
  try {
    audio.currentTime = 0;
  } catch {
    // The media may not have loaded enough metadata to seek.
  }
  audio.removeAttribute("src");
  audio.load();
}

export function AudioPreview({ projectId, audioRef, playMode }: Props) {
  const audioElementRef = useRef<HTMLAudioElement>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    let active = true;
    setUrl(null);
    setLoadError(false);

    if (!projectId) {
      setLoadError(true);
      return () => {
        active = false;
        releaseAudio(audioElementRef.current);
      };
    }

    mediaUrl(projectId, audioRef)
      .then((resolvedUrl) => {
        if (active) setUrl(resolvedUrl);
      })
      .catch(() => {
        if (active) setLoadError(true);
      });

    return () => {
      active = false;
      releaseAudio(audioElementRef.current);
    };
  }, [audioRef, projectId]);

  return (
    <div className="audio-preview">
      <audio
        ref={audioElementRef}
        className="audio-preview__player"
        src={url ?? undefined}
        controls
        controlsList="nodownload noplaybackrate noremoteplayback"
        preload="metadata"
        loop={playMode === "loop"}
        onLoadedMetadata={() => setLoadError(false)}
        onError={() => {
          if (url) setLoadError(true);
        }}
        aria-label="音频预听"
      />
      {loadError && (
        <Alert
          className="audio-preview__error"
          type="error"
          showIcon
          message={LOAD_ERROR_MESSAGE}
        />
      )}
    </div>
  );
}
