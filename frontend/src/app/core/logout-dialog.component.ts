import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-logout-dialog',
  standalone: true,
  template: `
    @if (open) {
      <div class="backdrop" role="presentation" (click)="cancelled.emit()">
        <section
          class="dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="logout-title"
          (click)="$event.stopPropagation()"
        >
          <p class="eyebrow">Cerrar sesion</p>
          <h2 id="logout-title">{{ pending ? 'Hay operaciones pendientes' : 'Desea salir?' }}</h2>
          <p>
            @if (pending) {
              Las operaciones pendientes de sincronizar se conservaran en este dispositivo.
            } @else {
              Se cerrara su sesion en este dispositivo.
            }
          </p>
          <div class="actions">
            <button type="button" class="ghost" (click)="cancelled.emit()">Cancelar</button>
            <button type="button" (click)="confirmed.emit()">Cerrar sesion</button>
          </div>
        </section>
      </div>
    }
  `,
  styles: `
    .backdrop {
      position: fixed;
      inset: 0;
      z-index: 1000;
      display: grid;
      place-items: center;
      padding: 1rem;
      background: rgba(15, 23, 42, 0.55);
      backdrop-filter: blur(4px);
    }

    .dialog {
      width: min(100%, 380px);
      border-radius: 18px;
      background: #ffffff;
      padding: 1.4rem;
      box-shadow: 0 24px 70px rgba(15, 23, 42, 0.24);
    }

    .eyebrow {
      margin: 0 0 0.4rem;
      color: #be185d;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    h2 {
      margin: 0;
      color: #111827;
      font-size: 1.3rem;
    }

    p {
      margin: 0.65rem 0 0;
      color: #4b5563;
      line-height: 1.5;
    }

    .actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.65rem;
      margin-top: 1.2rem;
    }

    button {
      min-height: 44px;
      border: 0;
      border-radius: 10px;
      background: #be185d;
      color: #ffffff;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }

    button.ghost {
      border: 1px solid #fbcfe8;
      background: #ffffff;
      color: #be185d;
    }
  `,
})
export class LogoutDialogComponent {
  @Input() open = false;
  @Input() pending = false;
  @Output() readonly confirmed = new EventEmitter<void>();
  @Output() readonly cancelled = new EventEmitter<void>();
}
