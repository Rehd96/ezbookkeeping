package models

// ProductAlias represents a mapping from a raw receipt item name to a normalized product, stored in database
type ProductAlias struct {
	AliasId         int64  `xorm:"PK"`
	Uid             int64  `xorm:"UNIQUE(UQE_product_alias_uid_raw_text) NOT NULL"`
	ProductId       int64  `xorm:"INDEX(IDX_product_alias_uid_product_id) NOT NULL"`
	RawText         string `xorm:"VARCHAR(255) UNIQUE(UQE_product_alias_uid_raw_text) NOT NULL"`
	CreatedUnixTime int64
}
