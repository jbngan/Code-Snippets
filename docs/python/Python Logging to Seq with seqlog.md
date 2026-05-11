# Python Logging to Seq with `seqlog`

## Use `SeqLogHandler` directly — avoid `log_to_seq`

`seqlog.log_to_seq(override_root_logger=True)` calls `dictConfig` internally,
which resets all existing handlers (file, console). Use `SeqLogHandler` instead
and attach it manually alongside other handlers.

## Setup

```python
import logging
import seqlog

fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
root = logging.getLogger()
root.setLevel(logging.INFO)

handlers = [logging.FileHandler('app.log'), logging.StreamHandler()]

if SEQ_URL:
    seq_handler = seqlog.SeqLogHandler(
        server_url=SEQ_URL,
        api_key=SEQ_API_KEY,   # omit if no auth
        batch_size=10,
        auto_flush_timeout=5,  # seconds
    )
    seq_handler.setLevel(logging.INFO)
    handlers.append(seq_handler)

for h in handlers:
    h.setFormatter(fmt)
    root.addHandler(h)

log = logging.getLogger(__name__)
```

## .env
```
SEQ_URL=http://your-seq-server:5341
SEQ_API_KEY=your-api-key
```
Leave SEQ_API_KEY empty if Seq has no auth required.
SEQ_URL absence disables Seq — file + console still work.
