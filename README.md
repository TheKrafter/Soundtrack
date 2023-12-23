<div align="center"><img src="src/assets/icon.png"></div>

# Soundtrack
A Discord Bot to play soundtracks in VC

Intended for Dungeons and Dragons campaigns, for cool music stuffs :).

## Roadmap

- [ ] Basic bot stuff
- [ ] Upload Tracks
    - [ ] Command to upload into/loop pair, set delay, and name
    - [ ] Flat file config to store above stuffs
    - [ ] Command to remove intro/loop pair by name
- [ ] Playing Tracks
    - [ ] Autocompletion for track names
    - [ ] Play
        1. Play intro track
        2. Wait for delay duration
        3. Loop the looped track forever
    - [ ] Pause
        - [ ] Pause
        - [ ] Stop at end of loop
        - [ ] Fade out and stop

## Running

#### Prerequisites

- `ffmpeg`
- `python3`

Flit: 
```
pip install -U flit
```

#### Install

*Note: Soundtrack has only been tested on Linux. While portability has been kept in mind, *

```sh
# Get the code
git clone https://github.com/TheKrafter/Soundtrack.git
cd Soundtrack

# Install (use `--symbolic` for development)
flit install

# Run
python3 -m soundtrack
```

## Notes

- Designed for use by a single server
- Audio is lossy (compressed)
- Titles must be valid YAML keys
- Files are stored in XDG Base Directories:
    - `config.yml` at `$XDG_CONFIG_HOME/soundtrack/config.yml`
    - Track files and `index.yml` track index are stored in `$XDG_DATA_HOME/soundtrack/`
- Can only be connected to 1 Voice Channel at a time

## License

Soundtrack, Copyright (c) 2023 Krafter Developer, is licensed under the MIT License.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.