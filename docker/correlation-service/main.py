from analysis import load_colcap, load_news, compute_correlation, save_results

def main():
    # Cargar datos
    colcap_df = load_colcap()
    news_df = load_news()

    # Calcular correlación agregada
    result = compute_correlation(colcap_df, news_df)

    # Guardar resultados
    save_results(result)

    print("Análisis completado")
    print(result)

if __name__ == "__main__":
    main()
