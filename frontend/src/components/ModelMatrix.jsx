export function ModelMatrix({ models }) {
  return (
    <section className="panel">
      <div className="panel-header"><span>Model Output Matrix</span><span className="panel-subtle">Availability, confidence, uncertainty and latency</span></div>
      <div className="table-wrap"><table className="matrix-table"><thead><tr><th>Model</th><th>Status</th><th>Prediction</th><th>Confidence</th><th>Uncertainty</th><th>Latency</th></tr></thead><tbody>{models.map((model) => <tr key={model.name}><td>{model.name}</td><td>{model.availability}</td><td>{model.predictedClass}</td><td>{model.confidence}%</td><td>{model.uncertainty}%</td><td>{model.latencyMs} ms</td></tr>)}</tbody></table></div>
    </section>
  )
}
