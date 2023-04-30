import base64
from dataclasses import dataclass


@dataclass
class Popup:
    image: str = None
    name: str = None
    width: str = "20"
    height: str = "20"
    popup_text: str = None

    def popup(self):
        encoded = base64.b64encode(open(self.image, "rb").read())

        html = (
            '<img src="data:image/png;base64,{}", alt={}, width={}, height={}>'.format
        )

        html_add = html(encoded.decode("UTF-8"), self.name, self.width, self.height)

        html = f"""
            <style>
                .tooltip {{
                position: relative;
                display: inline-block;
                border-bottom: 1px dotted grey;
                }}

                .tooltip .tooltiptext {{
                    visibility: hidden;
                    background-color: grey;
                    color: #fff;
                    text-align: center;
                    border-radius: 6px;
                    padding: 5px 0;
                    position: absolute;
                    z-index: 1;
                    top: 150%;
                    left: 50%;
                    margin-left: -60px;
                }}

                .tooltip .tooltiptext::after {{
                    content: "";
                    position: absolute;
                    bottom: 100%;
                    left: 50%;
                    margin-left: -5px;
                    border-width: 5px;
                    border-style: solid;
                    border-color: transparent transparent grey transparent;
                }}
                .tooltip:hover .tooltiptext {{
                visibility: visible;
                }}
                
                .tooltip .tooltiptext {{
                    opacity: 0;
                    transition: opacity 1s;
                }}

                .tooltip:hover .tooltiptext {{
                opacity: 1;
                }}
            </style>
            
            <a class="tooltip" > 
                {html_add}
                <span class="tooltiptext">{self.popup_text}</span>
            </a>
            """

        return html
