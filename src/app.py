import base64

import gradio as gr
import emission_calculator.calculator as ec


def validate_input(
    company_name: str,
    avg_electric_bill: float,
    avg_gas_bill: float,
    avg_transport_cost: float,
    monthly_waste_generated: float,
    recycled_waste_percent: float,
    annual_travel_kms: float,
    fuel_efficiency: float,
) -> None:
    """
    Comprehensive validation for input parameters with non-zero requirements
    """
    # Company Name Validation
    if not company_name or company_name.isspace():
        raise gr.Error("Company name cannot be empty or just whitespace!")

    if len(company_name) > 100:
        raise gr.Error("Company name is too long (maximum 100 characters)!")

    # Non-Zero Input Validation
    non_zero_fields = [
        ("Electricity Bill", avg_electric_bill),
        ("Gas Bill", avg_gas_bill),
        ("Transport Cost", avg_transport_cost),
        ("Monthly Waste", monthly_waste_generated),
        ("Annual Travel Distance", annual_travel_kms),
        ("Fuel Efficiency", fuel_efficiency),
    ]

    for name, value in non_zero_fields:
        try:
            float_val = float(value)
        except (TypeError, ValueError):
            raise gr.Error(f"{name} must be a valid number!")

        if float_val <= 0:
            raise gr.Error(f"{name} must be a positive number greater than zero!")

        # Additional realistic range checks
        if name == "Electricity Bill" and float_val > 10000:
            raise gr.Error(
                "Electricity bill seems unrealistically high. Please check the amount!"
            )

        if name == "Monthly Waste" and float_val > 1000:
            raise gr.Error(
                "Monthly waste generation seems extremely high. Please verify!"
            )

    # Percentage-specific validation
    try:
        recycled_percent = float(recycled_waste_percent)
    except (TypeError, ValueError):
        raise gr.Error("Recycled waste percentage must be a valid number!")

    if recycled_percent < 0 or recycled_percent > 100:
        raise gr.Error("Recycled waste percentage must be between 0 and 100!")

def compute(
    company_name: str,
    avg_electric_bill: float,
    avg_gas_bill: float,
    avg_transport_cost: float,
    monthly_waste_generated: float,
    recycled_waste_percent: float,
    annual_travel_kms: float,
    fuel_efficiency: float,
) -> tuple:
    """
    Compute carbon footprint with comprehensive input validation
    Returns summary HTML and base64 encoded image data
    """
    # Validate inputs first
    validate_input(
        company_name,
        avg_electric_bill,
        avg_gas_bill,
        avg_transport_cost,
        monthly_waste_generated,
        recycled_waste_percent,
        annual_travel_kms,
        fuel_efficiency,
    )

    # Proceed with calculation if validation passes
    df = ec.make_dataframe(
        company_name=company_name,
        avg_electric_bill=avg_electric_bill,
        avg_gas_bill=avg_gas_bill,
        avg_transport_bill=avg_transport_cost,
        monthly_waste_generated=monthly_waste_generated,
        recycled_waste_percent=recycled_waste_percent,
        annual_travel_kms=annual_travel_kms,
        fuel_efficiency=fuel_efficiency,
    )
    plot = ec.draw_report_figure(df)

    # Convert plot to base64 image
    img_data = base64.b64encode(
        plot.to_image(width=1400, height=800, format="png")
    ).decode("utf-8")

    # convert plot to pdf for downloading report
    file_path = f'./reports/{company_name.lower().replace(' ', '_')[:10]}_report.pdf'
    plot.write_image(file_path, width=1400, height=800)

    # Generate a summary HTML with embedded image
    summary = f"""
    <div style="max-width: 1400px; margin: 0 auto; font-family: Arial, sans-serif;">
        <h3 style="color: #ffffff;"> Carbon Footprint Summary for {company_name} </h3>
        <ul style="color: #666;">
            <li>🏭 <strong>Total Carbon Impact</strong>: Calculated based on your inputs</li>
            <li>💡 <strong>Energy Consumption</strong>: €{avg_electric_bill + avg_gas_bill:.2f}</li>
            <li>🚗 <strong>Transportation Emissions</strong>: {annual_travel_kms} km</li>
            <li>🗑️ <strong>Waste Management</strong>: {monthly_waste_generated} kg (Recycled: {recycled_waste_percent}%)</li>
        </ul>
        <img src="data:image/png;base64,{img_data}" style="max-width: 100%; height: auto;" alt="Carbon Footprint Report"/>
    </div>
    """
    download_button = gr.DownloadButton("Download Report", variant="secondary", visible=True, value=file_path)
    return summary, download_button


def create_carbon_footprint_app() -> gr.Blocks:
    with gr.Blocks(theme="soft") as demo:
        gr.Markdown("# 🌍 Carbon Footprint Calculator")

        # Hidden image download button
        download_button = gr.File(
            label="Download Carbon Footprint Report", type="binary", visible=False
        )

        with gr.Column():
            with gr.Column(scale=2):
                with gr.Column(variant="compact"):
                    company_name = gr.Textbox(
                        label="Company Name",
                        placeholder="Enter your company name",
                        info="Required: Full legal company name",
                    )
                with gr.Row():
                    with gr.Column(variant="compact"):
                        avg_electric_bill = gr.Number(
                            value=1.0,
                            label="Average Electricity Bill (€)",
                            minimum=0.01,
                            info="Monthly electricity expenses",
                        )
                        avg_gas_bill = gr.Number(
                            value=1.0,
                            label="Average Gas Bill (€)",
                            minimum=0.01,
                            info="Monthly natural gas expenses",
                        )
                        avg_transport_cost = gr.Number(
                            value=1.0,
                            label="Average Transport Cost (€)",
                            info="Monthly Fuel bill for transport",
                        )

                    with gr.Column(variant="compact"):
                        annual_travel_kms = gr.Number(
                            value=1.0,
                            label="Annual Business Travel (km)",
                            minimum=0.01,
                            info="Total kilometers traveled by employees",
                        )
                        fuel_efficiency = gr.Number(
                            value=1.0,
                            label="Vehicle Fuel Efficiency (L/100 km)",
                            minimum=0.01,
                            info="Average fleet fuel consumption",
                        )

                    with gr.Column(variant="compact"):
                        monthly_waste_generated = gr.Number(
                            value=1.0,
                            label="Monthly Waste Generated (kg)",
                            minimum=0.01,
                            info="Total waste produced monthly",
                        )
                        recycled_waste_percent = gr.Number(
                            value=0.0,
                            label="Recycled Waste (%)",
                            minimum=0.0,
                            maximum=100.0,
                            info="Percentage of waste recycled",
                        )

            with gr.Column(scale=1):
                output_plot = gr.HTML(label="Carbon Footprint Report")
                # Create a row for buttons
                with gr.Row():
                    submit_button = gr.Button("Generate Report", variant="primary")
                    download_button = gr.DownloadButton("Download Report", variant="secondary", visible=False)

        submit_button.click(
            fn=compute,
            inputs=[
                company_name,
                avg_electric_bill,
                avg_gas_bill,
                avg_transport_cost,
                monthly_waste_generated,
                recycled_waste_percent,
                annual_travel_kms,
                fuel_efficiency,
            ],
            outputs=[output_plot, download_button],
        )

    return demo


if __name__ == "__main__":
    create_carbon_footprint_app().launch()