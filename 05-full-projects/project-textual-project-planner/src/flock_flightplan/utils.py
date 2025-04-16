from io import StringIO
from rich.console import Console
from rich.text import Text  

from textual.widgets import Static
buffer = StringIO()
console = Console(file=buffer)



cli_text = Text()

def cli_init(log: Static):
    banner_text = Text(
        """
                                                                                                                         
    _/_/_/_/       _/       _/                     _/          _/                         _/                             
   _/             _/                  _/_/_/      _/_/_/    _/_/_/_/        _/_/_/       _/        _/_/_/      _/_/_/    
  _/_/_/         _/       _/       _/    _/      _/    _/    _/            _/    _/     _/      _/    _/      _/    _/   
 _/             _/       _/       _/    _/      _/    _/    _/            _/    _/     _/      _/    _/      _/    _/    
_/             _/       _/         _/_/_/      _/    _/      _/_/        _/_/_/       _/        _/_/_/      _/    _/     
                                      _/                                _/                                               
                                 _/_/                                  _/                                                

""",
        style="bold orange"
    )

    banner_text.append(Text("plan anything - implement everything - ｐｏｗｅｒｅｄ ｂｙ ＦＬＯＣＫ\n", style="bold white"))

    log.update(banner_text)




