import libcst as cst


def test_transformer_initialization(transformer):
    """Test transformer initialization with default settings."""
    assert transformer.current_class is None
    assert transformer.overwrite is True


def test_needs_docstring_no_existing(transformer):
    """Test needs_docstring when no docstring exists."""
    node = cst.parse_module('def test(): pass').body[0]
    assert transformer.needs_docstring(node) is True


def test_needs_docstring_existing(transformer):
    """Test needs_docstring when docstring exists."""
    node = cst.parse_module('def test():\n    """Existing docstring"""\n    pass').body[
        0
    ]
    assert transformer.needs_docstring(node) is False


def test_generate_docstring(transformer, test_function_sourcecode):
    """Test docstring generation for a function."""
    node = cst.parse_module(test_function_sourcecode).body[0]
    docstring = transformer.generate_docstring(node)
    assert isinstance(docstring, str)
    assert len(docstring) > 0


def test_insert_docstring(transformer):
    """Test docstring insertion into a function."""
    node = cst.parse_module('def test(): pass').body[0]
    docstring = 'Test function docstring'
    updated_node = transformer.insert_docstring(node, docstring)
    assert isinstance(updated_node, cst.FunctionDef)
    assert transformer._node_has_docstring(updated_node)


def test_class_context_tracking(transformer, test_class_sourcecode):
    """Test class context tracking during transformation."""
    module = cst.parse_module(test_class_sourcecode)
    transformer.visit_ClassDef(module.body[0])
    assert transformer.current_class == 'Calculator'


def test_progress_tracking(transformer, progress_tracker, test_function_sourcecode):
    """Test progress tracking during transformation."""
    transformer.progress_tracker = progress_tracker
    module = cst.parse_module(test_function_sourcecode)
    transformer.visit_FunctionDef(module.body[0])
    assert len(progress_tracker.tracked_object['current_file']) > 0


def test_transform_with_existing_docstring(transformer):
    """Test transformation of code with existing docstring."""
    code = 'def test():\n    """Existing docstring"""\n    pass'
    module = cst.parse_module(code)
    result = module.visit(transformer)
    assert (
        result.code == code
    )  # Should not modify existing docstring when overwrite=False


def test_transform_class_method(transformer, test_class_sourcecode):
    """Test transformation of a class method."""
    module = cst.parse_module(test_class_sourcecode)
    result = module.visit(transformer)
    assert isinstance(result, cst.Module)
    assert any(isinstance(node, cst.ClassDef) for node in result.body)
