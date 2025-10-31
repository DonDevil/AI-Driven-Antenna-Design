import flet as ft
from cst_interface.cst_driver import CSTDriver
from RDN_AI import TrainedAI
import time
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
    def generate_antenna(family, shape, freq, bandwidth, substrate, conductor, looprun=True):
        substrates = {
            'FR-4 (lossy)': (4.4, 0.0016),
            'Rogers RT-duroid 5880 (lossy)': (2.2, 0.001524),
            'Taconic TLY-3 (lossy)': (2.3, 0.00157)
        }
        er = substrates[substrate][0]
        sh = substrates[substrate][1]
        # 2) Build in CST
        cst = CSTDriver()
        firsttime = True
        # 1) Ask AI for params
        while looprun or firsttime:
            opt = ai.optimize_parameters(float(freq), float(bandwidth), eps_r=er, substrate_h=sh)
            params_dict = opt["dict"]
            numeric_params = opt["numeric"]  # [W,L,eps_eff,substrate_h,eps_r,feed_width]
            feed_type_label = opt["feed_type_label"]

            cst.standard_antenna(family, shape, freq, substrate, conductor, params_dict, retry=looprun, firsttime=firsttime)

            # 3) Export + parse S11 (best-effort)
            actual_Fr, actual_BW, s11_dip = cst.extract_s11_results(r"C:\Users\donde\AppData\Local\Temp\CSTDE1\Temp\DE\Untitled_0.cst")

            # If parsing failed, set placeholders and notify
            if actual_Fr is None:
                page.open(ft.SnackBar(ft.Text("CST export/parse failed — feedback not logged. Check export macro/path.")))
                page.update()
                return params_dict

            # 4) Log feedback to CSV
            ai.log_feedback(float(freq), float(bandwidth), numeric_params, feed_type_label, actual_Fr, actual_BW, s11_dip)
            # 5) Auto-correct predicted numeric params using the observed error
            corrected_numeric = ai.autocorrect_params(numeric_params, desired_Fr=float(freq), actual_Fr=actual_Fr,
                                                    desired_BW=float(bandwidth), actual_BW=actual_BW)
            # Build corrected param dict for a re-run
            corrected_params = params_dict.copy()
            corrected_params["patch_W"] = corrected_numeric[0]
            corrected_params["patch_L"] = corrected_numeric[1]
            corrected_params["eps_eff"] = corrected_numeric[2]
            corrected_params["substrate_h"] = corrected_numeric[3]
            corrected_params["eps_r"] = corrected_numeric[4]
            corrected_params["feed_width"] = corrected_numeric[5]
            
            # Optionally re-run in CST to see corrected result (set to True to auto-run)
            AUTO_RERUN_AFTER_CORRECT = False
            if AUTO_RERUN_AFTER_CORRECT:
                # small delay to let CST settle
                time.sleep(0.5)
                cst.standard_antenna(family, shape, freq, substrate, conductor, corrected_params, retry=True)
                # Try to re-export and parse again (optional)
                actual_Fr2, actual_BW2, s11_dip2 = cst.extract_s11_results(r"C:\Users\donde\AppData\Local\Temp\CSTDE1\Temp\DE\Untitled_0.cst")
                # log the corrected run as well
                if actual_Fr2 is not None:
                    ai.log_feedback(float(freq), float(bandwidth), corrected_numeric, feed_type_label, actual_Fr2, actual_BW2, s11_dip2)
                    page.open(ft.SnackBar(ft.Text(f"Initial: {actual_Fr:.3f} GHz / {s11_dip:.1f} dB. After correct: {actual_Fr2:.3f} GHz / {s11_dip2:.1f} dB")))
                    page.update()
                else:
                    page.open(ft.SnackBar(ft.Text(f"Initial: {actual_Fr:.3f} GHz / {s11_dip:.1f} dB. Correction applied but export failed.")))
                    page.update()
            else:
                page.open(ft.SnackBar(ft.Text(f"Result: {actual_Fr:.3f} GHz / {s11_dip:.1f} dB")))
                page.update()

            page.update()

            # 6) Retrain if enough feedback exists (synchronous)
            ai.retrain_if_needed()
            freq_tolerance = 0.03  # GHz, e.g., within 30 MHz
            bw_tolerance = 15      # MHz, e.g., within 15 MHz

            if abs(actual_Fr - float(freq)) < freq_tolerance and abs(actual_BW - float(bandwidth)) < bw_tolerance:
                return
            else:
                print("\nretring again!!!\n")
            firsttime = False

        # return params for any further use
        return params_dict


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
