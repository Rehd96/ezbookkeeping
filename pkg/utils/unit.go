package utils

import "strings"

// Base measurement units that product quantities are normalized to for comparison
const (
	UnitMilliliter = "ml"
	UnitGram       = "g"
	UnitPiece      = "pcs"
)

// unitConversionFactors maps a recognized raw unit token (lowercased) to its base unit
// and the multiplier needed to convert a quantity in that raw unit into the base unit
var unitConversionFactors = map[string]struct {
	BaseUnit string
	Factor   float64
}{
	"ml":          {UnitMilliliter, 1},
	"milliliter":  {UnitMilliliter, 1},
	"milliliters": {UnitMilliliter, 1},
	"cl":          {UnitMilliliter, 10},
	"l":           {UnitMilliliter, 1000},
	"liter":       {UnitMilliliter, 1000},
	"liters":      {UnitMilliliter, 1000},
	"litre":       {UnitMilliliter, 1000},
	"litres":      {UnitMilliliter, 1000},

	"mg":        {UnitGram, 0.001},
	"g":         {UnitGram, 1},
	"gram":      {UnitGram, 1},
	"grams":     {UnitGram, 1},
	"kg":        {UnitGram, 1000},
	"kilogram":  {UnitGram, 1000},
	"kilograms": {UnitGram, 1000},
	"oz":        {UnitGram, 28.3495},
	"ounce":     {UnitGram, 28.3495},
	"ounces":    {UnitGram, 28.3495},
	"lb":        {UnitGram, 453.592},
	"lbs":       {UnitGram, 453.592},
	"pound":     {UnitGram, 453.592},
	"pounds":    {UnitGram, 453.592},

	"pcs":    {UnitPiece, 1},
	"pc":     {UnitPiece, 1},
	"piece":  {UnitPiece, 1},
	"pieces": {UnitPiece, 1},
	"unit":   {UnitPiece, 1},
	"units":  {UnitPiece, 1},
	"pack":   {UnitPiece, 1},
	"packs":  {UnitPiece, 1},
	"ea":     {UnitPiece, 1},
	"each":   {UnitPiece, 1},
}

// NormalizeQuantityUnit converts a raw quantity and unit (as extracted from a receipt) into
// a normalized quantity expressed in one of the base units (ml, g, pcs). If the unit is
// unrecognized, it falls back to treating the item as a count of pieces so callers always
// get a usable normalized value, and ok is returned as false to signal the fallback was used.
func NormalizeQuantityUnit(quantity float64, unit string) (normalizedQuantity float64, normalizedUnit string, ok bool) {
	trimmedUnit := strings.ToLower(strings.TrimSpace(unit))

	if trimmedUnit == "" {
		return quantity, UnitPiece, false
	}

	conversion, found := unitConversionFactors[trimmedUnit]

	if !found {
		return quantity, UnitPiece, false
	}

	return quantity * conversion.Factor, conversion.BaseUnit, true
}
