from drafter import *
from dataclasses import dataclass, field
from chempy import Substance

set_website_title("Chemistry Companion")
set_site_information(
    author="James Hicks",
    description="Provide helpful and convinient information to chemistry students.",
    sources="Thanks to the Drafter docs and my study group.",
    planning="plan.pdf",
    links=["https://github.com/your-username/your-repository"]
)
hide_debug_information()
set_website_framed(False)

# ==========================
# Thermochemistry Data
# ==========================

DELTA_H = {
    "H2O": -285.8,
    "CO2": -393.5,
    "CH4": -74.8,
    "H2": 0.0,
    "O2": 0.0,
    "N2": 0.0,
}


# ==========================
# Dataclasses
# ==========================

@dataclass
class Species:
    formula: str
    coefficient: int
    molar_mass: float
    verified: bool
    mass: float
    moles: float


@dataclass
class State:
    equation: str
    reactants: list[Species]
    products: list[Species]

    actual_yield: float
    target_product: str

    limiting_reactant: str
    theoretical_yield: float
    percent_yield: float

    delta_h: float
    reaction_type: str

    error: str


# ==========================
# Helper Functions
# ==========================

def make_species(formula: str, coefficient: int) -> Species:
    """
    Creates a Species object from a chemical formula and
    stoichiometric coefficient. Uses Chempy to determine
    the molar mass of the compound.

    Args:
        formula: Chemical formula of the species.
        coefficient: Stoichiometric coefficient in the reaction.

    Returns:
        A populated Species object.
    """
    return Species(
        formula=formula,
        coefficient=coefficient,
        molar_mass=Substance.from_formula(formula).mass,
        verified=True,
        mass=0.0,
        moles=0.0
    )


def parse_side(side: str) -> list:
    """
    Parses one side of a balanced chemical equation and
    converts each compound into a Species object.

    Args:
        side: Reactant or product side of the equation.

    Returns:
        A list of Species objects.
    """

    result = []

    pieces = side.split("+")

    for piece in pieces:

        piece = piece.strip()

        parts = piece.split()

        if len(parts) == 1:

            coefficient = 1
            formula = parts[0]

        else:

            coefficient = int(parts[0])
            formula = parts[1]

        result.append(
            make_species(formula, coefficient)
        )

    return result


def find_limiting(state: State):
    """
    Determines the limiting reactant by comparing the
    mole-to-coefficient ratio for each reactant.

    Args:
        state: Current application state.

    Returns:
        A tuple containing the limiting reactant formula
        and the reaction extent.
    """
    smallest_ratio = None
    limiting = ""

    for species in state.reactants:

        ratio = (
            species.moles /
            species.coefficient
        )

        if smallest_ratio is None:

            smallest_ratio = ratio
            limiting = species.formula

        elif ratio < smallest_ratio:

            smallest_ratio = ratio
            limiting = species.formula

    return limiting, smallest_ratio


def compute_heat(state: State) -> float:
    """
    Calculates the heat of reaction using standard heats
    of formation stored in the DELTA_H dictionary.

    Args:
        state: Current application state.

    Returns:
        Heat of reaction in kilojoules (kJ).
    """
    products_total = 0
    reactants_total = 0

    for species in state.products:

        if species.formula in DELTA_H:

            products_total += (
                DELTA_H[species.formula]
                * species.coefficient
            )

    for species in state.reactants:

        if species.formula in DELTA_H:

            reactants_total += (
                DELTA_H[species.formula]
                * species.coefficient
            )

    return products_total - reactants_total


# ==========================
# Routes
# ==========================

@route
def index(state: State) -> Page:
    """
    Displays the home page and allows the user to enter
    a balanced chemical equation for analysis.
    """
    return Page(state, [

        "StoichioLab",
        "\n",

        "Enter a balanced reaction:",
        TextBox(
            "equation",
            state.equation
        ),

        "\n",

        state.error,

        Button(
            "Parse Equation",
            "parse_equation"
        )
    ])


@route
def parse_equation(
    state: State,
    equation: str
) -> Page:
    """
    Validates and parses the user-entered equation,
    creates reactant and product Species objects,
    and stores them in the application state.

    Args:
        state: Current application state.
        equation: Balanced chemical equation entered
                  by the user.

    Returns:
        The equation review page or an error page.
    """
    state.error = ""

    if "->" not in equation:

        state.error = (
            "Error: Equation must contain ->"
        )

        return index(state)

    state.equation = equation

    state.reactants = []
    state.products = []

    try:

        left, right = equation.split("->")

        state.reactants = parse_side(left)

        state.products = parse_side(right)

    except:

        state.error = (
            "Equation format invalid."
        )

        return index(state)

    return equation_review(state)


@route
def equation_review(state: State) -> Page:
    """
    Displays the parsed reactants and products along
    with their molar masses for user verification.

    Args:
        state: Current application state.

    Returns:
        An equation review page.
    """
    contents = [

        "Equation Review",
        "\n",

        state.equation,
        "\n",

        "Reactants:"
    ]

    for species in state.reactants:

        contents.append(

            f"{species.formula} "
            f"(MM={species.molar_mass:.2f} g/mol)"
        )

    contents.append("\nProducts:")

    for species in state.products:

        contents.append(

            f"{species.formula} "
            f"(MM={species.molar_mass:.2f} g/mol)"
        )

    contents.append(
        Button(
            "Continue",
            "masses"
        )
    )

    contents.append(
        Button(
            "Compound Info",
            "compound_info"
        )
    )

    return Page(state, contents)


@route
def masses(state: State) -> Page:
    """
    Displays input fields for reactant masses and
    actual product yield.

    Args:
        state: Current application state.

    Returns:
        A page for entering mass data.
    """
    species_names = ""

    for species in state.reactants:

        species_names += (
            species.formula + " "
        )

    return Page(state, [

        "Mass Entry",
        "\n",

        "Enter reactant masses (grams)",
        "\n",

        f"Order: {species_names}",
        "\n",

        "Example: 10,80",
        "\n",

        TextBox(
            "masses_input",
            ""
        ),

        "\nActual Product Harvested (g)",

        TextBox(
            "actual_yield",
            "0"
        ),

        "\n",

        Button(
            "Calculate",
            "calculate"
        )
    ])


@route
def calculate(
    state: State,
    masses_input: str,
    actual_yield: str
) -> Page:
    """
    Performs stoichiometric calculations including
    moles, limiting reactant determination, theoretical
    yield, percent yield, and reaction thermochemistry.

    Args:
        state: Current application state.
        masses_input: Comma-separated reactant masses.
        actual_yield: Actual mass of product obtained.

    Returns:
        The results page containing all calculations.
    """
    values = masses_input.split(",")

    if len(values) != len(state.reactants):

        state.error = (
            "Incorrect number of masses."
        )

        return masses(state)

    for i in range(len(state.reactants)):

        species = state.reactants[i]

        species.mass = float(values[i])

        if species.mass <= 0:

            state.error = (
                "Masses must be greater than 0."
            )

            return masses(state)

        species.moles = (
            species.mass
            /
            species.molar_mass
        )

    state.actual_yield = float(actual_yield)

    limiting, extent = (
        find_limiting(state)
    )

    state.limiting_reactant = (
        limiting
    )

    product = state.products[0]

    theoretical_moles = (
        extent *
        product.coefficient
    )

    state.theoretical_yield = (
        theoretical_moles
        * product.molar_mass
    )

    if state.theoretical_yield > 0:

        state.percent_yield = (

            state.actual_yield
            /
            state.theoretical_yield

        ) * 100

    else:

        state.percent_yield = 0

    state.delta_h = (
        compute_heat(state)
    )

    if state.delta_h < 0:

        state.reaction_type = (
            "Exothermic"
        )

    else:

        state.reaction_type = (
            "Endothermic"
        )

    return results(state)


@route
def results(state: State) -> Page:
    """
    Displays stoichiometric and thermochemical results
    for the analyzed reaction.

    Args:
        state: Current application state.

    Returns:
        A page showing calculation results.
    """
    return Page(state, [

        "Results",
        "\n",

        f"Limiting Reactant: "
        f"{state.limiting_reactant}",

        "\n",

        f"Theoretical Yield: "
        f"{state.theoretical_yield:.2f} g",

        "\n",

        f"Actual Yield: "
        f"{state.actual_yield:.2f} g",

        "\n",

        f"Percent Yield: "
        f"{state.percent_yield:.2f}%",

        "\n",

        f"Reaction Heat: "
        f"{state.delta_h:.2f} kJ",

        "\n",

        f"Type: "
        f"{state.reaction_type}",

        "\n",

        Button(
            "Species Information",
            "compound_info"
        ),

        Button(
            "New Reaction",
            "reset"
        )
    ])


@route
def compound_info(state: State) -> Page:
    """
    Displays detailed information about all reactants
    and products including formulas and molar masses.

    Args:
        state: Current application state.

    Returns:
        A page containing species information.
    """
    contents = [

        "Species Information",
        "\n"
    ]

    species_list = (
        state.reactants +
        state.products
    )

    # REQUIRED LOOP
    for species in species_list:

        contents.append(
            f"Formula: {species.formula}"
        )

        contents.append(
            f"Molar Mass: "
            f"{species.molar_mass:.2f}"
        )

        contents.append(
            f"Verified: "
            f"{species.verified}"
        )

        contents.append("\n")

    contents.append(
        Button(
            "Return",
            "equation_review"
        )
    )

    return Page(
        state,
        contents
    )


@route
def reset(state: State) -> Page:
    """
    Resets the application state and starts a new
    reaction analysis.

    Args:
        state: Current application state.

    Returns:
        The home page with cleared values.
    """
    state.equation = ""

    state.reactants = []

    state.products = []

    state.actual_yield = 0

    state.target_product = ""

    state.limiting_reactant = ""

    state.theoretical_yield = 0

    state.percent_yield = 0

    state.delta_h = 0

    state.reaction_type = ""

    state.error = ""

    return index(state)


# ==========================
# Initial State
# ==========================

start_server(
    State(
        equation="",
        reactants=[],
        products=[],
        actual_yield=0,
        target_product="",
        limiting_reactant="",
        theoretical_yield=0,
        percent_yield=0,
        delta_h=0,
        reaction_type="",
        error=""
    )
)
