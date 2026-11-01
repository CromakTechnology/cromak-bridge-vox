================================================================================
                    CROMAK BRIDGE VOX - MÓDULO FFMPEG
================================================================================

Para o correto funcionamento dos recursos de áudio, transcrição de voz pelo 
microfone, síntese e download/conversão de mídia (YouTube/MP3), esta pasta 
deve conter os binários oficiais do FFmpeg para Windows (64-bits).

--------------------------------------------------------------------------------
ARQUIVOS NECESSÁRIOS NESTA PASTA:
--------------------------------------------------------------------------------
1. ffmpeg.exe
2. ffprobe.exe

--------------------------------------------------------------------------------
COMO OBTER OS ARQUIVOS:
--------------------------------------------------------------------------------
1. Acesse o site oficial de builds do FFmpeg:
   https://www.gyan.dev/ffmpeg/builds/ ou https://ffmpeg.org/download.html
2. Baixe o pacote "ffmpeg-release-essentials.zip" (ou build completa).
3. Abra a pasta "bin" do arquivo compactado.
4. Copie os executáveis "ffmpeg.exe" e "ffprobe.exe" diretamente para esta pasta:
   plugins/ffmpeg/

--------------------------------------------------------------------------------
ESTRUTURA FINAL ESPERADA:
--------------------------------------------------------------------------------
plugins/
└── ffmpeg/
    ├── ffmpeg.exe       <-- (Colocar aqui)
    ├── ffprobe.exe      <-- (Colocar aqui)
    └── LEIAME.txt

Observação: No instalador oficial distribuído em .exe para o usuário final,
esses binários já acompanham o aplicativo compilado prontos para uso.
================================================================================