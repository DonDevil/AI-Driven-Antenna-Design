import flet as ft
from cst_interface.cst_driver import CSTDriver
from RDN_AI import TrainedAI

ai = TrainedAI()

def main(page: ft.Page):
    # Window configuration
    page.title = "AI Antenna Optimization System"
    page.window_width = 600
    page.window_height = 400
    page.window_resizable = False
    page.padding = 0
    page.bgcolor = ft.Colors.TRANSPARENT

    # ---- Initialize SnackBar ----
    page.snack_bar = ft.SnackBar(content=ft.Text(""))  # Initialize an empty SnackBar

    # ---- Common background ----
    def background(content):
        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#3b82f6", "#9333ea"],  # Blue → Purple gradient
            ),
            content=ft.Row(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        expand=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[content],
                    )
                ]
            ),
        )

    # ---- Function to handle antenna generation ----
    def generate_antenna(family, shape, freq, bandwidth, substrate, conductor):
        substrates = {
            'FR-4 (lossy)': (4.4, 0.0016),
            'Rogers4350': (3.66, 0.001524),
            'Rogers5880': (2.2, 0.00157),
            'TaconicTLY': (2.2, 0.0015)
        }
        er=substrates[substrate][0]
        sh = substrates[substrate][1]

        param = ai.optimize_parameters(float(freq), float(bandwidth), eps_r=er, substrate_h=sh)
        print(param)
        cst = CSTDriver()
        cst.standard_antenna(family, shape, freq, substrate, conductor, param)

        page.update()

        return param

    # ---- HOME PAGE ----
    def home_view():
        return ft.View(
            route="/",
            controls=[
                background(
                    ft.Container(
                        expand=False,
                        border_radius=30,
                        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                        shadow=ft.BoxShadow(
                            blur_radius=30,
                            spread_radius=5,
                            color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
                        ),
                        border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
                        padding=50,
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=30,
                            controls=[
                                ft.Text(
                                    "AI Antenna Optimization System",
                                    size=26,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Text(
                                    "Choose what you'd like to do:",
                                    size=16,
                                    color=ft.Colors.WHITE70,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.ElevatedButton(
                                    text="Create New Antenna",
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=20),
                                        padding=20,
                                        bgcolor=ft.Colors.BLUE_ACCENT_400,
                                        color=ft.Colors.WHITE,
                                    ),
                                    width=250,
                                    on_click=lambda e: page.go("/create"),
                                ),
                                ft.ElevatedButton(
                                    text="Optimize Existing Antenna",
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=20),
                                        padding=20,
                                        bgcolor=ft.Colors.PURPLE_ACCENT_400,
                                        color=ft.Colors.WHITE,
                                    ),
                                    width=250,
                                    on_click=lambda e: page.go("/optimize"),
                                ),
                            ],
                        ),
                    )
                )
            ]
        )


    # ---- CREATE NEW ANTENNA PAGE ----
    def create_view():
        antenna_families = ["Microstrip Patch", "Monopole", "Dipole", "Array"]
        shapes = ["Rectangular", "Circular", "Meandered", "Fractal"]
        substrates = ["FR-4 (lossy)", "Rogers RT-duroid 5880 (lossy)", "Taconic TLY-3 (lossy)"]
        conductors = ["Copper (annealed)", "Aluminum", "Silver"]

        # Input fields
        antenna_family_dropdown = ft.Dropdown(
            label="Antenna Family",
            options=[ft.dropdown.Option(i) for i in antenna_families],
            width=400,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        )

        shape_dropdown = ft.Dropdown(
            label="Shape",
            options=[ft.dropdown.Option(i) for i in shapes],
            width=400,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        )

        freq_field = ft.TextField(
            label="Resonant Frequency (GHz)",
            width=400,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
        )

        bandwidth_field = ft.TextField(
            label="Bandwidth (MHz)",
            width=400,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
        )

        substrate_dropdown = ft.Dropdown(
            label="Substrate Material",
            options=[ft.dropdown.Option(i) for i in substrates],
            width=400,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        )

        conductor_dropdown = ft.Dropdown(
            label="Conductor Material",
            options=[ft.dropdown.Option(i) for i in conductors],
            width=400,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        )

        return ft.View(
            route="/create",
            controls=[
                background(
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=600,
                                border_radius=30,
                                bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                                shadow=ft.BoxShadow(
                                    blur_radius=30,
                                    spread_radius=5,
                                    color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
                                ),
                                border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
                                padding=30,
                                content=ft.Column(
                                    spacing=15,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(
                                            "Create New Antenna",
                                            size=24,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE,
                                        ),
                                        antenna_family_dropdown,
                                        shape_dropdown,
                                        freq_field,
                                        bandwidth_field,
                                        substrate_dropdown,
                                        conductor_dropdown,
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            spacing=20,
                                            controls=[
                                                ft.ElevatedButton(
                                                    text="Generate Design",
                                                    style=ft.ButtonStyle(
                                                        bgcolor=ft.Colors.BLUE_ACCENT_400,
                                                        color=ft.Colors.WHITE,
                                                        shape=ft.RoundedRectangleBorder(radius=20),
                                                        padding=20,
                                                    ),
                                                    on_click=lambda e: generate_antenna(
                                                        antenna_family_dropdown.value,
                                                        shape_dropdown.value,
                                                        freq_field.value,
                                                        bandwidth_field.value,
                                                        substrate_dropdown.value,
                                                        conductor_dropdown.value
                                                    ),
                                                ),
                                                ft.ElevatedButton(
                                                    text="Back",
                                                    style=ft.ButtonStyle(
                                                        bgcolor=ft.Colors.GREY_700,
                                                        color=ft.Colors.WHITE,
                                                        shape=ft.RoundedRectangleBorder(radius=20),
                                                        padding=20,
                                                    ),
                                                    on_click=lambda e: page.go("/"),
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    )
                )
            ],
        )

    # ---- OPTIMIZE ANTENNA PAGE ----
    def optimize_view():
        existing_antennas = ["Antenna 1", "Antenna 2", "Antenna 3"]  # Example list

        return ft.View(
            route="/optimize",
            controls=[
                background(
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=600,
                                border_radius=30,
                                bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                                shadow=ft.BoxShadow(
                                    blur_radius=30,
                                    spread_radius=5,
                                    color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
                                ),
                                border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
                                padding=30,
                                content=ft.Column(
                                    spacing=15,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(
                                            "Optimize Existing Antenna",
                                            size=24,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE,
                                        ),
                                        ft.Dropdown(
                                            label="Select Antenna",
                                            options=[ft.dropdown.Option(i) for i in existing_antennas],
                                            width=400,
                                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                                        ),
                                        ft.TextField(
                                            label="Target Resonant Frequency (GHz)",
                                            width=400,
                                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                                            color=ft.Colors.WHITE,
                                        ),
                                        ft.TextField(
                                            label="Target Bandwidth (MHz)",
                                            width=400,
                                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                                            color=ft.Colors.WHITE,
                                        ),
                                        ft.Dropdown(
                                            label="Substrate Material",
                                            options=[ft.dropdown.Option(i) for i in ["FR4", "Rogers 5880", "Duroid", "Taconic"]],
                                            width=400,
                                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                                        ),
                                        ft.Dropdown(
                                            label="Conductor Material",
                                            options=[ft.dropdown.Option(i) for i in ["Copper", "Aluminum", "Silver"]],
                                            width=400,
                                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                                        ),
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            spacing=20,
                                            controls=[
                                                ft.ElevatedButton(
                                                    text="Optimize",
                                                    style=ft.ButtonStyle(
                                                        bgcolor=ft.Colors.PURPLE_ACCENT_400,
                                                        color=ft.Colors.WHITE,
                                                        shape=ft.RoundedRectangleBorder(radius=20),
                                                        padding=20,
                                                    ),
                                                    on_click=lambda e: page.snack_bar.open(
                                                        ft.SnackBar(ft.Text("Optimization coming soon!"))
                                                    ),
                                                ),
                                                ft.ElevatedButton(
                                                    text="Back",
                                                    style=ft.ButtonStyle(
                                                        bgcolor=ft.Colors.GREY_700,
                                                        color=ft.Colors.WHITE,
                                                        shape=ft.RoundedRectangleBorder(radius=20),
                                                        padding=20,
                                                    ),
                                                    on_click=lambda e: page.go("/"),
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    )
                )
            ],
        )

    # ---- Handle navigation ----
    def route_change(route):
        page.views.clear()
        if page.route == "/create":
            page.views.append(create_view())
        elif page.route == "/optimize":
            page.views.append(optimize_view())
        else:
            page.views.append(home_view())
        page.views[0].expand = True
        page.update()

    page.on_route_change = route_change
    page.go("/")

ft.app(target=main)
