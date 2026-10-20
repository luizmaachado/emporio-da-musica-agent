"""Splitting the store manual into numbered sections."""
from emporio.data.policies import (
    INTERNAL_SECTIONS,
    load_policy_sections,
    parse_sections,
)
from emporio.domain.policies import PolicySection

# Sections 1 to 6, so that a test can start at a later number like the real manual does.
FILLER = "\n".join(f"{i}. Seção {i}\nTexto {i}." for i in range(1, 7))


def sections_after_filler(body: str) -> list[PolicySection]:
    return parse_sections([f"{FILLER}\n{body}"])[6:]


# Synthetic pages


def test_text_before_the_first_heading_is_the_cover_and_is_dropped():
    pages = ["EMPÓRIO DA MÚSICA\nManual\n1. Sobre\nTexto da loja."]

    (section,) = parse_sections(pages)

    assert section.number == "1"
    assert section.text == "Texto da loja."


def test_page_headers_and_footers_are_removed_even_inside_a_section():
    pages = [
        "1. Sobre\nPrimeira parte.\nPágina 1",
        "Empório da Música Manual de Políticas e Procedimentos\nSegunda parte.",
    ]

    (section,) = parse_sections(pages)

    assert section.text == "Primeira parte.\nSegunda parte."


def test_a_subsection_carries_the_title_of_its_parent():
    parent, child = sections_after_filler(
        "7. Formas de Pagamento\nIntro.\n7.1 Regras de Parcelamento\nAté 12x."
    )

    assert (parent.number, parent.parent_title) == ("7", None)
    assert child.parent_title == "Formas de Pagamento"
    assert child.heading == "7.1 Regras de Parcelamento (Formas de Pagamento)"


def test_a_section_with_no_text_of_its_own_is_left_out():
    sections = sections_after_filler("7. Frete\n7.1 Região\nGrátis acima de R$ 500,00.")

    assert [s.number for s in sections] == ["7.1"]


def test_a_numbered_list_inside_a_section_is_not_split_into_sections():
    sections = sections_after_filler(
        "7. Atendimento\nCanal principal.\n7.1 Fluxo\n"
        "1. Saudação: cumprimentar.\n2. Entendimento: identificar.\n3. Consulta: buscar.\n"
        "8. Garantia\n8.1 Legal\n90 dias."
    )

    assert [s.number for s in sections] == ["7", "7.1", "8.1"]
    assert "3. Consulta: buscar." in sections[1].text


def test_money_and_numbers_at_the_start_of_a_line_are_not_headings():
    (section,) = sections_after_filler(
        "7. Pagamento\nParcelas acima de\n2.000,00 podem ser combinadas.\n50,00 é o mínimo."
    )

    assert "2.000,00 podem" in section.text


# The real manual


def test_the_real_manual_has_the_expected_sections_in_order():
    sections = load_policy_sections(include_internal=True)

    assert [s.number for s in sections] == [
        "1", "1.1", "1.2", "2", "3", "3.1", "4", "4.1", "4.2", "4.3", "4.4",
        "5.1", "5.2", "5.3", "6.1", "6.2", "7", "7.1", "7.2", "7.3",
        "8.1", "8.2", "8.3", "9", "10",
    ]  # fmt: skip


def test_customer_sections_leave_out_only_the_service_flow_and_closing_notes():
    numbers_ = {section.number for section in load_policy_sections()}

    assert numbers_.isdisjoint(INTERNAL_SECTIONS)
    assert {"7", "7.1", "7.3"} <= numbers_  # response time, complaint deadline, special cases


def test_the_payment_table_keeps_one_row_per_line():
    section = next(s for s in load_policy_sections() if s.number == "3")

    assert "PIX Pagamento à vista 5% de desconto sobre o preço de" in section.text


def test_installment_rules_are_complete():
    section = next(s for s in load_policy_sections() if s.number == "3.1")

    for rule in ("até 3x", "4x a 6x", "7x a 12x", "R$ 2.000,00"):
        assert rule in section.text


def test_no_page_header_or_footer_leaks_into_any_section():
    for section in load_policy_sections(include_internal=True):
        assert "Página " not in section.text
        assert "Manual de Políticas e Procedimentos" not in section.text


def test_a_section_split_across_pages_is_joined():
    section = next(s for s in load_policy_sections() if s.number == "5.2")

    assert "Jadlog" in section.text
    assert "recusar o recebimento" in section.text


def test_company_data_has_the_address_and_the_store_phone():
    section = next(s for s in load_policy_sections() if s.number == "1.2")

    assert "Rua 14 de Maio, 3200" in section.text
    assert "(67) 3341-4444" in section.text


def test_the_excluded_sections_are_still_the_ones_we_meant_to_exclude():
    """Sections are excluded by number, so a renumbered manual must not go unnoticed."""
    titles = {s.number: s.title for s in load_policy_sections(include_internal=True)}

    assert titles["7.2"] == "Fluxo de Atendimento Padrão"
    assert titles["10"] == "Disposições Finais"
