#!/usr/bin/env python
"""
Demonstration script for the Measurements OCR Batch Workflow.

This script shows how to use the workflow to extract pool measurements
and customer names from OCR text.
"""

from godman_ai.engine import AgentEngine


def demo_basic_usage():
    """Demonstrate basic workflow usage."""
    print("=" * 70)
    print("Measurements OCR Batch Workflow - Demo")
    print("=" * 70)
    print()
    
    # Initialize the engine
    print("1. Initializing Agent Engine...")
    engine = AgentEngine()
    print(f"   ✓ Loaded {len(engine.workflows)} workflows")
    print()
    
    # Show available workflows
    print("2. Available workflows:")
    for workflow_name in engine.workflows.keys():
        print(f"   - {workflow_name}")
    print()
    
    # Demonstrate measurement extraction
    print("3. Testing measurement extraction:")
    from godman_ai.workflows.measurements_ocr_batch import MeasurementsOCRBatchWorkflow
    
    workflow = MeasurementsOCRBatchWorkflow(engine=engine)
    
    test_cases = [
        "Pool dimensions: 20 x 40\nCustomer: John Smith",
        "Owner: Jane Doe\nPool size: 15.5' x 30.5' feet",
        "Name: Bob Johnson\nDimensions: 25 by 50",
        "Pool: 10 x 200",  # Unusual aspect ratio
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n   Test case {i}:")
        print(f"   Text: {text[:50]}...")
        
        measurements, confidence = workflow.extract_measurements(text)
        customer = workflow.extract_customer_name(text)
        
        if measurements:
            errors = workflow.validate_measurements(measurements)
            print(f"   ✓ Measurements: {measurements[0]} x {measurements[1]} ft")
            print(f"   ✓ Confidence: {confidence:.2f}")
            
            if errors:
                print(f"   ⚠ Validation warnings:")
                for error in errors:
                    print(f"      - {error}")
        else:
            print(f"   ✗ No measurements found")
        
        if customer:
            print(f"   ✓ Customer: {customer}")
        else:
            print(f"   ✗ No customer name found")
    
    print()
    print("=" * 70)
    print("Demo completed!")
    print("=" * 70)


def demo_validation_rules():
    """Demonstrate validation rules."""
    print("\n" + "=" * 70)
    print("Validation Rules Demo")
    print("=" * 70)
    print()
    
    from godman_ai.workflows.measurements_ocr_batch import MeasurementsOCRBatchWorkflow
    
    workflow = MeasurementsOCRBatchWorkflow(engine=None)
    
    print(f"Validation bounds:")
    print(f"  - Minimum dimension: {workflow.MIN_DIMENSION} ft")
    print(f"  - Maximum dimension: {workflow.MAX_DIMENSION} ft")
    print(f"  - Aspect ratio warning threshold: 10:1")
    print()
    
    test_cases = [
        ((20.0, 40.0), "Valid pool dimensions"),
        ((5.0, 5.0), "Minimum valid size"),
        ((200.0, 200.0), "Maximum valid size"),
        ((2.0, 40.0), "Too small width"),
        ((250.0, 300.0), "Too large"),
        ((10.0, 150.0), "Unusual aspect ratio"),
    ]
    
    for measurements, description in test_cases:
        errors = workflow.validate_measurements(measurements)
        print(f"{description}: {measurements[0]} x {measurements[1]} ft")
        
        if errors:
            print(f"  Status: ✗ Invalid")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  Status: ✓ Valid")
        print()


if __name__ == "__main__":
    demo_basic_usage()
    demo_validation_rules()
