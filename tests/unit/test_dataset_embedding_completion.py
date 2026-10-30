import pytest
from scripts.complete_dataset_embeddings import validate_vectors


def test_invalid_remote_vectors_rejected_before_db_write():
    for vectors in ([[float('nan')]*1024], [[0.0]*1024], [[True]*1024], [[1.0]*1000], []):
        with pytest.raises(ValueError): validate_vectors(vectors,1)


def test_finite_complete_vectors_accepted():
    validate_vectors([[0.25]*1024,[0.5]*1024],2)
    with pytest.raises(ValueError):validate_vectors([[0.25]*1024],2)
