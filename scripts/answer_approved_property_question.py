"""Answer policy questions using authorized, approved source versions."""

from functools import partial

from answer_property_question import answer_question
from build_approved_context import build_approved_context
from retrieve_documents import IDENTITY_DATA


def answer_approved_question(
    identity_id,
    query,
    provider,
    *,
    document_folder,
    approval_path,
    identity_folder=IDENTITY_DATA,
):
    context_builder = partial(
        build_approved_context,
        approval_path=approval_path,
    )

    return answer_question(
        identity_id,
        query,
        provider,
        identity_folder=identity_folder,
        document_folder=document_folder,
        context_builder=context_builder,
    )