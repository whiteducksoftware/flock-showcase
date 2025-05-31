from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from dspy import Image
from flock.core import Flock, FlockAgent, FlockFactory, flock_component, flock_type
from flock.core.flock_module import FlockModule, FlockModuleConfig
from flock.routers.default.default_router import DefaultRouterConfig
from pydantic import BaseModel, Field


@flock_type
class FlockImage(BaseModel):
    image: Image


@flock_type
class ImagePart(BaseModel):
    image_part: str = Field(description="Part of the image to draw")
    list_of_coordinates: list[tuple[float, float]] = Field(
        default_factory=list,
        description="List of coordinates to connect to create a part of the image. X<10 - Y<10 - coordinates are floats - use this accuracy for better results",
    )
    matplotlib_color: str = Field(
        default="b", description="Color of the line in the plot"
    )


############################################################
# MatplotDrawerModule
############################################################


class MatplotDrawerModuleConfig(FlockModuleConfig):
    pass


@flock_component(config_class=MatplotDrawerModuleConfig)
class MatplotDrawerModule(FlockModule):
    image: Image = None
    image_parts: list[ImagePart] = None
    counter: int = 0

    async def draw_image(self, agent, input, output):
        self.counter += 1

        self.image_parts = output["list_of_all_image_parts"]

        plt.figure(figsize=(10, 10))

        for image_part in self.image_parts:
            coordinates = np.array(
                image_part.list_of_coordinates
            )  # Convert list to numpy array
            if len(coordinates) > 1:
                plt.plot(
                    coordinates[:, 0],
                    coordinates[:, 1],
                    marker="x",
                    linestyle="-",
                    markersize=5,
                    color=image_part.matplotlib_color,
                )

        plt.axis("equal")  # Keep aspect ratio
        plt.grid(True)

        save_path = f"plot_{self.counter}.png"
        plt.savefig(save_path, dpi=300)

        self.image = Image.from_file(save_path)

        plt.show()

    # if there is a previous image, load it and give it to the agent
    # manipulate agent input and description
    async def load_prev_image(self, agent: FlockAgent, inputs):
        if self.image is not None:
            agent.description = "Improves the image by adding new parts to the previous image and/or changing them. Will ALWAYS do some changes to the image."
            agent.input = "subject_to_draw: str, prev_image: FlockImage | result of rendered image parts, prev_image_parts: list[ImagePart] | previously generated image parts"
            image = FlockImage(image=self.image)
            inputs["prev_image"] = image
            inputs["prev_image_parts"] = self.image_parts

        return inputs

    async def on_post_evaluate(
        self,
        agent: FlockAgent,
        inputs: dict[str, Any],
        context: Any | None = None,
        result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self.draw_image(agent, inputs, result)

        return result

    async def on_pre_evaluate(
        self,
        agent: FlockAgent,
        inputs: dict[str, Any],
        context: Any | None = None,
    ) -> dict[str, Any]:
        return await self.load_prev_image(agent, inputs)


############################################################


# global variables
MODEL = "azure/gpt-4.1"


flock = Flock(model=MODEL)


the_painter = FlockFactory.create_default_agent(
    name="the_painter",
    input="subject_to_draw: str",
    description="Draws an image by connecting the coordinates of the image parts. 0/0 is bottom left corner - 10/10 is top right corner",
    output="list_of_all_image_parts: list[ImagePart] | list of all image parts to draw by connecting the coordinates",
)


the_painter.add_component(
    config_instance=DefaultRouterConfig(hand_off="the_painter"), component_name="router"
)

the_painter.add_component(
    config_instance=MatplotDrawerModuleConfig(), component_name="matplot_drawer"
)

flock.add_agent(the_painter)

result = flock.run(agent=the_painter, input={"subject_to_draw": "a house"})
