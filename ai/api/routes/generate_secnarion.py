from manim import *

class AccidentScene(Scene):
    def construct(self):
        # Draw the road (simple cross intersection)
        road_horizontal = Rectangle(width=8, height=2, color=GRAY, fill_opacity=0.5)
        road_vertical = Rectangle(width=2, height=8, color=GRAY, fill_opacity=0.5)
        self.play(Create(road_horizontal), Create(road_vertical))

        # Create two cars
        car1 = Rectangle(width=1.2, height=0.6, color=BLUE, fill_opacity=1).shift(LEFT*4)
        car2 = Rectangle(width=1.2, height=0.6, color=RED, fill_opacity=1).shift(UP*4)

        car1_label = Text("Car A", font_size=24).next_to(car1, DOWN)
        car2_label = Text("Car B", font_size=24).next_to(car2, LEFT)

        self.play(FadeIn(car1), FadeIn(car2))

        # Animate both cars moving *at the same time*
        self.play(
            car1.animate.shift(RIGHT*4),
            car2.animate.shift(DOWN*4),
            run_time=5
        )
        # After collision, cars stop slightly rotated (like real crash)
        self.play(
            car1.animate.rotate(0.3).shift(DOWN*0.5),
            car2.animate.rotate(-0.3).shift(RIGHT*0.5),
            run_time=2
        )

