# Lumen ASR with the proposed Fourier picker

This is an unsigned Windows x64 contributor build of [Lumen ASR PR 206](https://github.com/fakechris/lumen-asr/pull/206). It was built from commit 850949c0986261b3c7c0b4f957af57c0e5d90f8f in a public fork. Lumen's maintainers publish official installers in [their release channel](https://github.com/fakechris/lumen-asr/releases).

Use a fresh Windows user or test VM. The unmodified installer uses Lumen's normal application identity and settings directory. Check the installer hash against SHA256SUMS. Use your organization's normal software installation policy.

Open Settings, select speech recognition and choose **下载 Oruk Fourier 2B 英语模型**. The first install downloads ten files (2.41 GB) directly from [Oruk's original model card](https://huggingface.co/oruk/oruk-fourier-2b). Weights are distributed separately under Oruk’s model license. The folder can be selected offline once the download finishes.

The archive includes desktop source and its GPL-3.0-only license. Cargo.lock and Cargo.toml pin its dependencies, including the [shared downloader source](https://github.com/Nathan-Roll1/lumen-suite/tree/5858800c940707387fdfa830ab5f0cc9f9b41ddd). The CI workflow and test live separately from the source used for the installer.
