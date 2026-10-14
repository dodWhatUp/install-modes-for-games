"""Use the existing owner's safety/journal, not a second implementation."""
from pathlib import Path
import sys
try:
    import GameToolJournal
    from game_mod_ops import safety
except ModuleNotFoundError as exc:
    if exc.name not in {'GameToolJournal', 'game_mod_ops', 'game_mod_ops.safety'}:
        raise
    compat = Path(__file__).absolute().parents[2] / 'compat'
    if not compat.is_dir():
        raise RuntimeError('The host GameToolJournal and game_mod_ops.safety are required.') from exc
    sys.path.append(str(compat))
    import GameToolJournal
    from game_mod_ops import safety
Journal = GameToolJournal.Journal
inspect_journal = GameToolJournal.inspect_journal
Error = safety.ModError
require = safety.require
no_links = safety.no_links
contained = safety.contained
safe_relative = safety.safe_relative
slug = safety.slug
strict_json = safety.strict_json
canonical = safety.canonical
object_hash = safety.object_hash
json_new = safety.json_new
write_new = safety.write_new
read_json = safety.read_json
local_lock = safety.local_lock
