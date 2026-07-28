import React from 'react';
import './Products.css';
import imgSolventes from '../assets/solventes.png';
import imgAcidos from '../assets/acidos.png';
import imgBases from '../assets/bases.png';
import imgReagentes from '../assets/reagentes.png';

const categorias = [
    {
        imagem: imgSolventes,
        nome: 'Solventes industriais',
        descricao: 'Solventes de alta pureza para diluição, limpeza industrial e formulação, com controle rígido de teor de umidade.'
    },
    {
        imagem: imgAcidos,
        nome: 'Ácidos',
        descricao: 'Ácidos inorgânicos e orgânicos para tratamento de superfície, síntese química e correção de processo.'
    },
    {
        imagem: imgBases,
        nome: 'Bases',
        descricao: 'Soluções alcalinas para neutralização, tratamento de efluentes e processos petroquímicos.'
    },
    {
        imagem: imgReagentes,
        nome: 'Reagentes especializados',
        descricao: 'Reagentes sob medida para agricultura, tratamento de água e aplicações analíticas específicas.'
    }
];

const Products = () => {
    return (
        <section id="produtos" className="products">
            <span className="section-eyebrow">Catálogo</span>
            <h2 className="section-title">Um portfólio pensado para operação contínua</h2>
            <p className="section-subtitle">
                Cada categoria abaixo tem FISPQ própria e lote rastreável — fale com
                nosso time comercial para a lista completa e condições de fornecimento.
            </p>

            <div className="products-grid">
                {categorias.map((c, i) => (
                    <div className="product-card" key={i}>
                        <div className="product-image-wrap">
                            <img src={c.imagem} alt={c.nome} className="product-image" />
                        </div>
                        <h3>{c.nome}</h3>
                        <p>{c.descricao}</p>
                    </div>
                ))}
            </div>
        </section>
    );
};

export default Products;
